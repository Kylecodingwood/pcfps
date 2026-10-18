package com.pcfps.preview;

import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Regression tests for {@link LasPreviewSubprocessRunner} stdout draining (pipe deadlock avoidance).
 *
 * @author PCFPS
 * @date 2026-05-08
 */
class LasPreviewSubprocessRunnerTest {

    private static final int LARGE_STDOUT_BYTE_COUNT = 70_000;

    @Test
    void drainChildStdoutWithByteCap_retainsAllWhenUnderCap() {
        byte[] payloadBytes = "hello-stdout".getBytes(StandardCharsets.UTF_8);
        ByteArrayInputStream childStdoutStream = new ByteArrayInputStream(payloadBytes);
        ByteArrayOutputStream captureBuffer = new ByteArrayOutputStream();
        AtomicReference<IOException> drainFailureRef = new AtomicReference<>();
        LasPreviewSubprocessRunner.drainChildStdoutWithByteCap(
                childStdoutStream,
                captureBuffer,
                10_000L,
                drainFailureRef
        );
        assertNull(drainFailureRef.get());
        assertEquals("hello-stdout", captureBuffer.toString(StandardCharsets.UTF_8));
    }

    @Test
    void drainChildStdoutWithByteCap_recordsFailureAndTruncatesWhenOverCap() {
        byte[] payloadBytes = new byte[5000];
        for (int byteIndex = 0; byteIndex < payloadBytes.length; byteIndex++) {
            payloadBytes[byteIndex] = (byte) 7;
        }
        ByteArrayInputStream childStdoutStream = new ByteArrayInputStream(payloadBytes);
        ByteArrayOutputStream captureBuffer = new ByteArrayOutputStream();
        AtomicReference<IOException> drainFailureRef = new AtomicReference<>();
        LasPreviewSubprocessRunner.drainChildStdoutWithByteCap(
                childStdoutStream,
                captureBuffer,
                1000L,
                drainFailureRef
        );
        assertNotNull(drainFailureRef.get());
        assertEquals(1000, captureBuffer.size());
    }

    @Test
    void largeChildStdoutWithConcurrentDrain_completesWithoutDeadlock() throws Exception {
        assumePython3Available();
        ProcessBuilder processBuilder = new ProcessBuilder(
                "python3",
                "-c",
                "import sys\n"
                        + "sys.stdout.buffer.write(b'x' * "
                        + LARGE_STDOUT_BYTE_COUNT
                        + ")\n"
                        + "sys.stdout.buffer.flush()\n"
        );
        processBuilder.redirectErrorStream(true);
        Process childProcess = processBuilder.start();
        ByteArrayOutputStream capturedStdoutBuffer = new ByteArrayOutputStream();
        AtomicReference<IOException> stdoutDrainFailureRef = new AtomicReference<>();
        Thread stdoutDrainThread = new Thread(
                () -> LasPreviewSubprocessRunner.drainChildStdoutWithByteCap(
                        childProcess.getInputStream(),
                        capturedStdoutBuffer,
                        10_000_000L,
                        stdoutDrainFailureRef
                ),
                "test-las-preview-stdout-drain"
        );
        stdoutDrainThread.setDaemon(true);
        stdoutDrainThread.start();
        boolean finishedWithinDeadline = childProcess.waitFor(60, TimeUnit.SECONDS);
        stdoutDrainThread.join(60_000);
        assertTrue(finishedWithinDeadline, "child process should exit; pipe deadlock would time out");
        assertNull(stdoutDrainFailureRef.get(), () -> String.valueOf(stdoutDrainFailureRef.get()));
        assertEquals(0, childProcess.exitValue());
        assertEquals(LARGE_STDOUT_BYTE_COUNT, capturedStdoutBuffer.size());
    }

    private static void assumePython3Available() throws InterruptedException {
        try {
            Process probeProcess = new ProcessBuilder("python3", "-c", "pass").start();
            boolean probeFinished = probeProcess.waitFor(15, TimeUnit.SECONDS);
            Assumptions.assumeTrue(probeFinished && probeProcess.exitValue() == 0);
        } catch (IOException ioException) {
            Assumptions.assumeTrue(false);
        }
    }
}
