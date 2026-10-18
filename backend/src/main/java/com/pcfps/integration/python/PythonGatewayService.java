package com.pcfps.integration.python;

/**
 * Abstraction over the Python REST worker. Replace implementation for real HTTP client.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
public interface PythonGatewayService {

    /**
     * Submits a job to Python and returns an external job identifier for polling.
     *
     * @param command paths and task reference
     * @return external job id
     */
    String submitJob(PythonJobSubmitCommand command);

    /**
     * Submits a segment or classify job on an existing LAS path.
     *
     * @param command derived paths, kind, algorithm, and parameters
     * @return external job id for polling (same {@code GET /jobs/{id}} as filter jobs)
     */
    String submitDerivedJob(PythonDerivedJobSubmitCommand command);

    /**
     * Polls processing state for the given external job.
     *
     * @param externalJobId id returned from {@link #submitJob(PythonJobSubmitCommand)}
     * @return current phase and optional error
     */
    PythonJobStatusView fetchStatus(String externalJobId);
}
