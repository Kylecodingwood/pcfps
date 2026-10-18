package com.pcfps.integration.python;

import com.pcfps.job.FilterMethod;

import java.util.UUID;

/**
 * Payload sent to the Python worker when submitting a filter job (Java-side view).
 *
 * @param taskId             internal task id
 * @param inputLasPath       absolute path to source LAS on server
 * @param outputBasePath     directory where Python should write outputs
 * @param filterMethod       algorithm token for the worker
 * @param sorNeighborCount   SOR {@code k} (ignored when method is ROR)
 * @param sorStdRatio        SOR std ratio (ignored when method is ROR)
 * @param rorRadius          ROR radius in LAS units (ignored when method is SOR)
 * @param rorMinNeighbors    ROR minimum neighbors (ignored when method is SOR)
 * @author PCFPS
 * @date 2026-04-12
 */
public record PythonJobSubmitCommand(
        UUID taskId,
        String inputLasPath,
        String outputBasePath,
        FilterMethod filterMethod,
        int sorNeighborCount,
        double sorStdRatio,
        double rorRadius,
        int rorMinNeighbors
) {
}
