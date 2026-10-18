package com.pcfps.integration.python;

import java.util.Map;
import java.util.UUID;

/**
 * Payload for Python {@code POST /derived-jobs} (segment / classify on existing LAS).
 *
 * @param taskId         Spring task UUID
 * @param inputLasPath   absolute path to input LAS (typically parent {@code FILTERED_LAS})
 * @param outputBasePath task output directory (worker writes {@code derived.las} here)
 * @param jobKind        {@code segment} or {@code classify}
 * @param algorithm      e.g. {@code euclidean_cluster}, {@code pmf}
 * @param paramsJsonMap  merged algorithm parameters (snake_case keys)
 * @author PCFPS
 * @date 2026-05-10
 */
public record PythonDerivedJobSubmitCommand(
        UUID taskId,
        String inputLasPath,
        String outputBasePath,
        String jobKind,
        String algorithm,
        Map<String, Object> paramsJsonMap
) {
}
