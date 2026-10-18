package com.pcfps.job;

/**
 * Point-cloud outlier filter algorithm selected when the task is created.
 *
 * <p>Values are persisted as {@code VARCHAR} on {@code filter_task.filter_method}.
 * The Python gateway expects lowercase tokens {@code sor} / {@code ror}.
 *
 * @author PCFPS
 * @date 2026-05-08
 */
public enum FilterMethod {

    /**
     * Statistical outlier removal (SOR): neighbors {@code k} and standard-deviation ratio.
     */
    SOR,

    /**
     * Radius outlier removal (ROR): search radius and minimum neighbor count.
     */
    ROR;

    /**
     * @return token accepted by {@code python_gateway} {@code JobSubmitPayload.filter_method}
     */
    public String toPythonGatewayToken() {
        return name().toLowerCase();
    }
}
