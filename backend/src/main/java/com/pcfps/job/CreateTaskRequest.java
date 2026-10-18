package com.pcfps.job;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

/**
 * Request body to create a filter task from an on-server LAS path and optional filter tuning.
 *
 * <p>Omitted numeric fields are replaced by server defaults at creation time. Configuration is
 * immutable after the task row is inserted.
 *
 * @param inputLasPath      absolute path to existing LAS file (trusted environment)
 * @param filterMethod      optional; defaults to {@link FilterMethod#SOR}
 * @param sorNeighborCount  SOR neighbor count {@code k} (optional)
 * @param sorStdRatio       SOR standard deviation ratio (optional)
 * @param rorRadius         ROR search radius in LAS XY units (optional)
 * @param rorMinNeighbors   ROR minimum neighbors inside radius (optional)
 * @author PCFPS
 * @date 2026-04-12
 */
public record CreateTaskRequest(
        @NotBlank String inputLasPath,
        FilterMethod filterMethod,
        @Min(1) Integer sorNeighborCount,
        @DecimalMin(value = "0.0", inclusive = false) Double sorStdRatio,
        @DecimalMin(value = "0.0", inclusive = false) Double rorRadius,
        @Min(0) Integer rorMinNeighbors
) {
}
