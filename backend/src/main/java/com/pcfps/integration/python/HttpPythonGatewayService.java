package com.pcfps.integration.python;

import com.pcfps.job.FilterMethod;
import com.pcfps.integration.python.remote.PythonJobCreatedResponse;
import com.pcfps.integration.python.remote.PythonRemoteJobStatus;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Calls the real Python FastAPI worker via HTTP.
 *
 * @author PCFPS
 * @date 2026-05-08
 */
@Service
@Profile("!mock-python")
public class HttpPythonGatewayService implements PythonGatewayService {

    private static final Logger log = LoggerFactory.getLogger(HttpPythonGatewayService.class);

    private static final Duration SUBMIT_TIMEOUT = Duration.ofSeconds(60);
    private static final Duration POLL_TIMEOUT = Duration.ofSeconds(60);

    private final WebClient pythonFilterWebClient;

    public HttpPythonGatewayService(WebClient pythonFilterWebClient) {
        this.pythonFilterWebClient = pythonFilterWebClient;
    }

    /**
     * Submits a LAS filter job to the Python worker.
     *
     * @param command paths and task id
     * @return external job id for polling
     */
    @Override
    public String submitJob(PythonJobSubmitCommand command) {
        Map<String, Object> requestBodyMap = new LinkedHashMap<>();
        requestBodyMap.put("external_business_task_id", command.taskId().toString());
        requestBodyMap.put("input_las_path", command.inputLasPath());
        String outputLasAbsolutePath = java.nio.file.Paths.get(command.outputBasePath(), "filtered.las")
                .toAbsolutePath()
                .toString();
        requestBodyMap.put("output_result_path", outputLasAbsolutePath);
        FilterMethod filterMethod = command.filterMethod();
        requestBodyMap.put("filter_method", filterMethod.toPythonGatewayToken());
        requestBodyMap.put("sor_neighbor_count", command.sorNeighborCount());
        requestBodyMap.put("sor_std_ratio", command.sorStdRatio());
        requestBodyMap.put("ror_radius", command.rorRadius());
        requestBodyMap.put("ror_min_neighbors", command.rorMinNeighbors());
        log.info(
                "Submitting Python filter job taskId={} inputLasPath={} outputLasPath={} filterMethod={}",
                command.taskId(),
                command.inputLasPath(),
                outputLasAbsolutePath,
                filterMethod
        );
        try {
            PythonJobCreatedResponse createdResponse = pythonFilterWebClient.post()
                    .uri("/jobs")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(requestBodyMap)
                    .retrieve()
                    .bodyToMono(PythonJobCreatedResponse.class)
                    .block(SUBMIT_TIMEOUT);
            if (createdResponse == null || createdResponse.externalPythonJobUuid() == null
                    || createdResponse.externalPythonJobUuid().isBlank()) {
                log.error("Python submit returned empty body taskId={}", command.taskId());
                throw new IllegalStateException("Python submit returned empty external_python_job_uuid");
            }
            log.info(
                    "Python job accepted taskId={} externalPythonJobUuid={}",
                    command.taskId(),
                    createdResponse.externalPythonJobUuid()
            );
            return createdResponse.externalPythonJobUuid();
        } catch (WebClientResponseException exception) {
            log.error(
                    "Python submit HTTP error taskId={} status={} body={}",
                    command.taskId(),
                    exception.getStatusCode().value(),
                    exception.getResponseBodyAsString(),
                    exception
            );
            throw new IllegalStateException(
                    "Python submit failed: HTTP " + exception.getStatusCode().value() + " "
                            + exception.getResponseBodyAsString(),
                    exception
            );
        }
    }

    /**
     * Submits segment/classify job to {@code POST /derived-jobs}.
     *
     * @param command derived job payload
     * @return external job uuid
     */
    @Override
    public String submitDerivedJob(PythonDerivedJobSubmitCommand command) {
        Map<String, Object> requestBodyMap = new LinkedHashMap<>();
        requestBodyMap.put("external_business_task_id", command.taskId().toString());
        requestBodyMap.put("input_las_path", command.inputLasPath());
        String outputLasAbsolutePath = java.nio.file.Paths.get(command.outputBasePath(), "derived.las")
                .toAbsolutePath()
                .toString();
        requestBodyMap.put("output_result_path", outputLasAbsolutePath);
        requestBodyMap.put("job_kind", command.jobKind());
        requestBodyMap.put("algorithm", command.algorithm());
        for (Map.Entry<String, Object> entry : command.paramsJsonMap().entrySet()) {
            requestBodyMap.put(entry.getKey(), entry.getValue());
        }
        log.info(
                "Submitting Python derived job taskId={} jobKind={} algorithm={} inputLasPath={} outputLasPath={}",
                command.taskId(),
                command.jobKind(),
                command.algorithm(),
                command.inputLasPath(),
                outputLasAbsolutePath
        );
        try {
            PythonJobCreatedResponse createdResponse = pythonFilterWebClient.post()
                    .uri("/derived-jobs")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(requestBodyMap)
                    .retrieve()
                    .bodyToMono(PythonJobCreatedResponse.class)
                    .block(SUBMIT_TIMEOUT);
            if (createdResponse == null || createdResponse.externalPythonJobUuid() == null
                    || createdResponse.externalPythonJobUuid().isBlank()) {
                log.error("Python derived submit returned empty body taskId={}", command.taskId());
                throw new IllegalStateException("Python derived submit returned empty external_python_job_uuid");
            }
            log.info(
                    "Python derived job accepted taskId={} externalPythonJobUuid={}",
                    command.taskId(),
                    createdResponse.externalPythonJobUuid()
            );
            return createdResponse.externalPythonJobUuid();
        } catch (WebClientResponseException exception) {
            log.error(
                    "Python derived submit HTTP error taskId={} status={} body={}",
                    command.taskId(),
                    exception.getStatusCode().value(),
                    exception.getResponseBodyAsString(),
                    exception
            );
            throw new IllegalStateException(
                    "Python derived submit failed: HTTP " + exception.getStatusCode().value() + " "
                            + exception.getResponseBodyAsString(),
                    exception
            );
        }
    }

    /**
     * Polls Python worker state for the given external job id.
     *
     * @param externalJobId id returned from submit
     * @return phase and optional error message for {@link com.pcfps.job.TaskService}
     */
    @Override
    public PythonJobStatusView fetchStatus(String externalJobId) {
        try {
            PythonRemoteJobStatus remoteStatus = pythonFilterWebClient.get()
                    .uri("/jobs/{id}", externalJobId)
                    .retrieve()
                    .bodyToMono(PythonRemoteJobStatus.class)
                    .block(POLL_TIMEOUT);
            if (remoteStatus == null || remoteStatus.lifecycleStateMachineToken() == null) {
                log.error("Python poll returned empty body externalJobId={}", externalJobId);
                return new PythonJobStatusView("FAILED", "Empty status from Python worker", null);
            }
            String phaseToken = remoteStatus.lifecycleStateMachineToken().trim();
            if ("FAILED".equalsIgnoreCase(phaseToken)) {
                String combinedMessage = buildFailureMessage(remoteStatus);
                log.warn("Python job FAILED externalJobId={} message={}", externalJobId, combinedMessage);
                return new PythonJobStatusView("FAILED", combinedMessage, null);
            }
            return new PythonJobStatusView(phaseToken.toUpperCase(), null, remoteStatus.metricsBundle());
        } catch (WebClientResponseException exception) {
            if (exception.getStatusCode().value() == 404) {
                log.warn("Python poll unknown job externalJobId={}", externalJobId);
                return new PythonJobStatusView("FAILED", "Unknown external job id: " + externalJobId, null);
            }
            log.error(
                    "Python poll HTTP error externalJobId={} status={}",
                    externalJobId,
                    exception.getStatusCode().value(),
                    exception
            );
            return new PythonJobStatusView(
                    "FAILED",
                    "Python poll HTTP " + exception.getStatusCode().value() + ": " + exception.getResponseBodyAsString(),
                    null
            );
        }
    }

    private static String buildFailureMessage(PythonRemoteJobStatus remoteStatus) {
        String errorCode = remoteStatus.errorCodeStableStringOptional();
        String errorMessage = remoteStatus.errorMessageHumanPlainOptional();
        if (errorCode != null && errorMessage != null) {
            return errorCode + ": " + errorMessage;
        }
        if (errorMessage != null) {
            return errorMessage;
        }
        if (errorCode != null) {
            return errorCode;
        }
        return "Python job failed";
    }
}
