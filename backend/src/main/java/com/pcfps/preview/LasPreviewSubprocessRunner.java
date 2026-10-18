package com.pcfps.preview;

import com.pcfps.common.BusinessException;
import com.pcfps.config.PreviewProperties;
import com.pcfps.preview.dto.PointPreviewResponse;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Invokes the bundled Python LAS sampler and maps stdout JSON into {@link PointPreviewResponse}.
 * <p>
 * Child stdout is drained on a background thread while the main thread {@link Process#waitFor(long, TimeUnit)}
 * runs, avoiding pipe deadlocks when JSON exceeds the OS pipe buffer size.
 *
 * @author PCFPS
 * @date 2026-05-07
 */
@Component
public class LasPreviewSubprocessRunner {

    private static final Logger log = LoggerFactory.getLogger(LasPreviewSubprocessRunner.class);

    private static final String SCRIPT_CLASSPATH = "scripts/las_preview_sample.py";

    private static final int STDOUT_COPY_BUFFER_BYTES = 8192;

    /**
     * After the child exits, join the stdout drain thread for at most this many milliseconds.
     */
    private static final int STDOUT_DRAIN_THREAD_JOIN_MS = 30_000;

    private final ObjectMapper objectMapper;

    public LasPreviewSubprocessRunner(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    /**
     * Runs laspy-based sampling for a LAS/LAZ path on disk.
     *
     * @param lasFilePath              absolute readable LAS path
     * @param maxPointCount            maximum points to return
     * @param previewProperties        runtime limits and python command
     * @param lasPreviewColorModeToken {@code native} or {@code classification} (4th CLI argument)
     * @param lasPreviewPaletteToken   {@code default} or {@code semantic_campus} (5th CLI argument)
     * @return parsed preview response from script stdout
     */
    public PointPreviewResponse runLasPreviewSubprocess(
            Path lasFilePath,
            int maxPointCount,
            PreviewProperties previewProperties,
            String lasPreviewColorModeToken,
            String lasPreviewPaletteToken
    ) {
        if (!previewProperties.lasPreviewEnabled()) {
            log.warn("LAS preview disabled by configuration path={}", lasFilePath);
            throw new BusinessException("LAS_PREVIEW_DISABLED", "LAS preview is disabled in server configuration");
        }
        ClassPathResource scriptResource = new ClassPathResource(SCRIPT_CLASSPATH);
        if (!scriptResource.exists()) {
            log.error("Missing classpath resource {}", SCRIPT_CLASSPATH);
            throw new BusinessException("LAS_PREVIEW_FAILED", "LAS preview script missing on server classpath");
        }
        Path temporaryScriptPath;
        try {
            temporaryScriptPath = Files.createTempFile("pcfps_las_preview_", ".py");
            try (InputStream scriptInputStream = scriptResource.getInputStream()) {
                Files.copy(scriptInputStream, temporaryScriptPath, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException ioException) {
            log.error("Failed to materialize LAS preview script: {}", ioException.getMessage(), ioException);
            throw new BusinessException("LAS_PREVIEW_FAILED", "Cannot prepare LAS preview script: " + ioException.getMessage());
        }
        Process lasPreviewProcess = null;
        Thread stdoutDrainThread = null;
        try {
            String paletteTokenNormalized = lasPreviewPaletteToken == null || lasPreviewPaletteToken.isBlank()
                    ? "default"
                    : lasPreviewPaletteToken.trim().toLowerCase();
            ProcessBuilder processBuilder = new ProcessBuilder(
                    previewProperties.pythonCommand(),
                    temporaryScriptPath.toAbsolutePath().toString(),
                    lasFilePath.toAbsolutePath().toString(),
                    Integer.toString(maxPointCount),
                    lasPreviewColorModeToken,
                    paletteTokenNormalized
            );
            processBuilder.redirectErrorStream(true);
            lasPreviewProcess = processBuilder.start();
            InputStream childStdoutStream = lasPreviewProcess.getInputStream();
            ByteArrayOutputStream capturedStdoutBuffer = new ByteArrayOutputStream();
            AtomicReference<IOException> stdoutDrainFailureRef = new AtomicReference<>();
            stdoutDrainThread = new Thread(
                    () -> drainChildStdoutWithByteCap(
                            childStdoutStream,
                            capturedStdoutBuffer,
                            previewProperties.maxFileBytes(),
                            stdoutDrainFailureRef
                    ),
                    "pcfps-las-preview-stdout-drain"
            );
            stdoutDrainThread.setDaemon(true);
            stdoutDrainThread.start();
            boolean finishedWithinDeadline = lasPreviewProcess.waitFor(
                    previewProperties.processTimeoutSeconds(),
                    TimeUnit.SECONDS
            );
            if (!finishedWithinDeadline) {
                lasPreviewProcess.destroyForcibly();
                log.error(
                        "LAS preview subprocess timed out after {}s path={}",
                        previewProperties.processTimeoutSeconds(),
                        lasFilePath
                );
                joinStdoutDrainThreadOrInterrupt(stdoutDrainThread);
                throw new BusinessException("LAS_PREVIEW_FAILED", "LAS preview subprocess timed out");
            }
            joinStdoutDrainThreadOrInterrupt(stdoutDrainThread);
            IOException stdoutDrainFailure = stdoutDrainFailureRef.get();
            if (stdoutDrainFailure != null) {
                log.error("LAS preview stdout drain failed path={}: {}", lasFilePath, stdoutDrainFailure.getMessage(), stdoutDrainFailure);
                throw new BusinessException("LAS_PREVIEW_FAILED", "LAS preview stdout drain failed: " + stdoutDrainFailure.getMessage());
            }
            int exitCode = lasPreviewProcess.exitValue();
            String combinedOutput = capturedStdoutBuffer.toString(StandardCharsets.UTF_8).trim();
            if (exitCode != 0) {
                log.error("LAS preview subprocess exitCode={} output={}", exitCode, combinedOutput);
                throw new BusinessException("LAS_PREVIEW_FAILED", "LAS preview failed: " + combinedOutput);
            }
            if (combinedOutput.isEmpty()) {
                throw new BusinessException("LAS_PREVIEW_FAILED", "LAS preview produced empty stdout");
            }
            return objectMapper.readValue(combinedOutput, PointPreviewResponse.class);
        } catch (InterruptedException interruptedException) {
            Thread.currentThread().interrupt();
            if (lasPreviewProcess != null) {
                lasPreviewProcess.destroyForcibly();
            }
            if (stdoutDrainThread != null) {
                joinStdoutDrainThreadOrInterrupt(stdoutDrainThread);
            }
            log.error("LAS preview interrupted: {}", interruptedException.getMessage(), interruptedException);
            throw new BusinessException("LAS_PREVIEW_FAILED", "LAS preview interrupted");
        } catch (IOException ioException) {
            log.error("LAS preview IO failure: {}", ioException.getMessage(), ioException);
            throw new BusinessException("LAS_PREVIEW_FAILED", "LAS preview IO failure: " + ioException.getMessage());
        } finally {
            try {
                Files.deleteIfExists(temporaryScriptPath);
            } catch (IOException deleteException) {
                log.warn("Could not delete temp script {}: {}", temporaryScriptPath, deleteException.getMessage());
            }
        }
    }

    /**
     * Waits for the stdout drain thread to finish reading the child stream (or interrupts it if still alive).
     *
     * @param stdoutDrainThread background reader thread
     */
    private static void joinStdoutDrainThreadOrInterrupt(Thread stdoutDrainThread) {
        try {
            stdoutDrainThread.join(STDOUT_DRAIN_THREAD_JOIN_MS);
        } catch (InterruptedException joinInterrupted) {
            Thread.currentThread().interrupt();
            stdoutDrainThread.interrupt();
            return;
        }
        if (stdoutDrainThread.isAlive()) {
            log.warn("LAS preview stdout drain thread still alive after {}ms; interrupting", STDOUT_DRAIN_THREAD_JOIN_MS);
            stdoutDrainThread.interrupt();
        }
    }

    /**
     * Copies {@code childStandardOutput} into {@code captureBuffer} until EOF, enforcing {@code maxCapturedBytes}
     * for stored payload. If the cap is exceeded, surplus bytes are read and discarded so the producer can finish.
     * Failures are recorded in {@code drainFailureRef} (first failure wins).
     *
     * @param childStandardOutput stream connected to the child process stdout (stderr may be merged)
     * @param captureBuffer       in-memory sink for captured bytes (subject to cap)
     * @param maxCapturedBytes    maximum bytes to retain in {@code captureBuffer}
     * @param drainFailureRef     holds the first {@link IOException} from draining, if any
     */
    static void drainChildStdoutWithByteCap(
            InputStream childStandardOutput,
            ByteArrayOutputStream captureBuffer,
            long maxCapturedBytes,
            AtomicReference<IOException> drainFailureRef
    ) {
        byte[] copyBuffer = new byte[STDOUT_COPY_BUFFER_BYTES];
        long bytesRetained = 0L;
        try {
            int chunkByteCount;
            while ((chunkByteCount = childStandardOutput.read(copyBuffer)) != -1) {
                if (bytesRetained >= maxCapturedBytes) {
                    drainFailureRef.compareAndSet(
                            null,
                            new IOException(
                                    "LAS preview stdout exceeded max captured bytes: " + maxCapturedBytes
                            )
                    );
                    continue;
                }
                long remainingRetentionBudget = maxCapturedBytes - bytesRetained;
                int retainByteCount = (int) Math.min(chunkByteCount, remainingRetentionBudget);
                if (retainByteCount > 0) {
                    captureBuffer.write(copyBuffer, 0, retainByteCount);
                    bytesRetained += retainByteCount;
                }
                if (retainByteCount < chunkByteCount) {
                    drainFailureRef.compareAndSet(
                            null,
                            new IOException(
                                    "LAS preview stdout exceeded max captured bytes: " + maxCapturedBytes
                            )
                    );
                }
            }
        } catch (IOException ioException) {
            drainFailureRef.compareAndSet(null, ioException);
        } finally {
            try {
                childStandardOutput.close();
            } catch (IOException closeException) {
                drainFailureRef.compareAndSet(null, closeException);
            }
        }
    }
}
