package com.pcfps.integration.python;

import com.pcfps.config.PcfpsProperties;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory mock Python worker for local development and thesis demo.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Service
@Profile("mock-python")
public class MockPythonGatewayService implements PythonGatewayService {

    private static final Logger log = LoggerFactory.getLogger(MockPythonGatewayService.class);

    private final PcfpsProperties pcfpsProperties;
    private final ConcurrentHashMap<String, MockJobState> jobStateMap = new ConcurrentHashMap<>();

    public MockPythonGatewayService(PcfpsProperties pcfpsProperties) {
        this.pcfpsProperties = pcfpsProperties;
    }

    @Override
    public String submitJob(PythonJobSubmitCommand command) {
        String externalJobId = UUID.randomUUID().toString();
        jobStateMap.put(externalJobId, new MockJobState(command.taskId(), 0, false, null));
        log.info(
                "Mock Python accepted job externalJobId={} taskId={} filterMethod={} sorK={} sorStd={} rorR={} rorMinN={}",
                externalJobId,
                command.taskId(),
                command.filterMethod(),
                command.sorNeighborCount(),
                command.sorStdRatio(),
                command.rorRadius(),
                command.rorMinNeighbors()
        );
        return externalJobId;
    }

    @Override
    public String submitDerivedJob(PythonDerivedJobSubmitCommand command) {
        String externalJobId = UUID.randomUUID().toString();
        jobStateMap.put(externalJobId, new MockJobState(command.taskId(), 0, true, command.algorithm()));
        log.info(
                "Mock Python accepted derived job externalJobId={} taskId={} jobKind={} algorithm={}",
                externalJobId,
                command.taskId(),
                command.jobKind(),
                command.algorithm()
        );
        return externalJobId;
    }

    @Override
    public PythonJobStatusView fetchStatus(String externalJobId) {
        MockJobState state = jobStateMap.get(externalJobId);
        if (state == null) {
            log.warn("Mock Python unknown externalJobId={}", externalJobId);
            return new PythonJobStatusView("FAILED", "Unknown external job id", null);
        }
        state.pollCount++;
        int threshold = pcfpsProperties.mockPython().succeedAfterTicks();
        if (state.pollCount >= threshold) {
            log.info("Mock Python succeeded externalJobId={} afterPolls={}", externalJobId, state.pollCount);
            if (state.derivedJob) {
                Map<String, Object> metricsBundle = new LinkedHashMap<>();
                metricsBundle.put("n_input", 1000);
                metricsBundle.put("n_output", 1000);
                metricsBundle.put("wall_time_sec", 0.01);
                if ("ml_rf_semantic".equalsIgnoreCase(state.derivedAlgorithm)) {
                    metricsBundle.put("algorithm_code", "ml_rf_semantic");
                    metricsBundle.put("n_ground", 120);
                    metricsBundle.put("n_building", 500);
                    metricsBundle.put("n_vegetation", 280);
                    metricsBundle.put("n_other", 100);
                    metricsBundle.put("ground_ratio", 0.12);
                } else if ("rule_semantic_campus".equalsIgnoreCase(state.derivedAlgorithm)) {
                    metricsBundle.put("algorithm_code", "rule_semantic_campus");
                    metricsBundle.put("n_ground", 120);
                    metricsBundle.put("n_building", 500);
                    metricsBundle.put("n_vegetation", 280);
                    metricsBundle.put("n_other", 100);
                    metricsBundle.put("ground_ratio", 0.12);
                } else if ("voxel_drop_ground".equalsIgnoreCase(state.derivedAlgorithm)) {
                    metricsBundle.put("algorithm_code", "voxel_drop_ground");
                    metricsBundle.put("n_input", 10000);
                    metricsBundle.put("n_output", 3200);
                    metricsBundle.put("n_removed_34", 2100);
                    metricsBundle.put("n_ground_in", 5000);
                    metricsBundle.put("n_ground_out", 400);
                    metricsBundle.put("ground_voxel_size_m", 0.5);
                    metricsBundle.put("compression_ratio", 10000.0 / 3200.0);
                } else {
                    metricsBundle.put("algorithm_code", "mock_derived");
                    metricsBundle.put("num_clusters", 3);
                }
                return new PythonJobStatusView("SUCCEEDED", null, metricsBundle);
            }
            return new PythonJobStatusView("SUCCEEDED", null, null);
        }
        return new PythonJobStatusView("RUNNING", null, null);
    }

    private static final class MockJobState {
        private final UUID taskId;
        private int pollCount;
        private final boolean derivedJob;
        private final String derivedAlgorithm;

        private MockJobState(UUID taskId, int pollCount, boolean derivedJob, String derivedAlgorithm) {
            this.taskId = taskId;
            this.pollCount = pollCount;
            this.derivedJob = derivedJob;
            this.derivedAlgorithm = derivedAlgorithm;
        }
    }
}
