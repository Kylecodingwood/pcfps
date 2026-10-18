package com.pcfps.integration.python.remote;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * JSON returned by Python worker {@code POST /jobs} (HTTP 202).
 *
 * @param externalPythonJobUuid worker-side job id used for polling
 * @author PCFPS
 * @date 2026-05-08
 */
public record PythonJobCreatedResponse(
        @JsonProperty("external_python_job_uuid")
        String externalPythonJobUuid
) {
}
