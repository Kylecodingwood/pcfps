package com.pcfps.integration.python.remote;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

/**
 * JSON returned by Python worker {@code GET /jobs/{id}}.
 *
 * @param lifecycleStateMachineToken RUNNING, SUCCEEDED, FAILED, etc.
 * @param errorCodeStableStringOptional stable code when failed
 * @param errorMessageHumanPlainOptional human message when failed
 * @param metricsBundle                optional Python {@code metrics_bundle} map when succeeded
 * @author PCFPS
 * @date 2026-05-08
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record PythonRemoteJobStatus(
        @JsonProperty("lifecycle_state_machine_token")
        String lifecycleStateMachineToken,
        @JsonProperty("error_code_stable_string_optional")
        String errorCodeStableStringOptional,
        @JsonProperty("error_message_human_plain_optional")
        String errorMessageHumanPlainOptional,
        @JsonProperty("metrics_bundle")
        Map<String, Object> metricsBundle
) {
}
