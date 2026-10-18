package com.pcfps.job;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Merges optional {@link CreateTaskRequest} filter fields with fixed defaults aligned to
 * {@code python_gateway} / {@code python_filter}.
 *
 * @author PCFPS
 * @date 2026-05-08
 */
public final class FilterParameterMergeSupport {

    public static final int DEFAULT_SOR_NEIGHBOR_COUNT = 20;
    public static final double DEFAULT_SOR_STD_RATIO = 1.0;
    public static final double DEFAULT_ROR_RADIUS = 0.5;
    public static final int DEFAULT_ROR_MIN_NEIGHBORS = 5;

    private FilterParameterMergeSupport() {
    }

    /**
     * Builds the effective filter snapshot for persistence and Python dispatch.
     *
     * @param createTaskRequest validated create request (nullable filter fields mean defaults)
     * @return merged method, JSON-shaped map, and summary line
     */
    public static FilterParameterMergeResult merge(CreateTaskRequest createTaskRequest) {
        FilterMethod chosenMethod = createTaskRequest.filterMethod() != null
                ? createTaskRequest.filterMethod()
                : FilterMethod.SOR;
        if (chosenMethod == FilterMethod.SOR) {
            int neighborCount = createTaskRequest.sorNeighborCount() != null
                    ? createTaskRequest.sorNeighborCount()
                    : DEFAULT_SOR_NEIGHBOR_COUNT;
            double stdRatio = createTaskRequest.sorStdRatio() != null
                    ? createTaskRequest.sorStdRatio()
                    : DEFAULT_SOR_STD_RATIO;
            Map<String, Object> paramsJsonMap = new LinkedHashMap<>();
            paramsJsonMap.put("sor_neighbor_count", neighborCount);
            paramsJsonMap.put("sor_std_ratio", stdRatio);
            String summaryLine = "SOR · k=" + neighborCount + " · std=" + stdRatio;
            return new FilterParameterMergeResult(FilterMethod.SOR, paramsJsonMap, summaryLine);
        }
        double radius = createTaskRequest.rorRadius() != null
                ? createTaskRequest.rorRadius()
                : DEFAULT_ROR_RADIUS;
        int minNeighbors = createTaskRequest.rorMinNeighbors() != null
                ? createTaskRequest.rorMinNeighbors()
                : DEFAULT_ROR_MIN_NEIGHBORS;
        Map<String, Object> paramsJsonMap = new LinkedHashMap<>();
        paramsJsonMap.put("ror_radius", radius);
        paramsJsonMap.put("ror_min_neighbors", minNeighbors);
        String summaryLine = "ROR · r=" + radius + " · minN=" + minNeighbors;
        return new FilterParameterMergeResult(FilterMethod.ROR, paramsJsonMap, summaryLine);
    }

    /**
     * @return summary for legacy rows with no persisted configuration (historically SOR 20/1.0)
     */
    public static String legacyHistoricalSummary() {
        return "SOR（历史默认） · k=" + DEFAULT_SOR_NEIGHBOR_COUNT + " · std=" + DEFAULT_SOR_STD_RATIO;
    }

    /**
     * Rebuilds the API summary string from a persisted method + JSON map (same shape as merge output).
     *
     * @param filterMethod persisted method; must not be null when map is non-null
     * @param paramsJsonMap persisted {@code filter_params_json}
     * @return one-line summary for {@link TaskResponseDto}
     */
    public static String summarizePersisted(FilterMethod filterMethod, Map<String, Object> paramsJsonMap) {
        if (filterMethod == FilterMethod.SOR) {
            int neighborCount = readInt(paramsJsonMap.get("sor_neighbor_count"), DEFAULT_SOR_NEIGHBOR_COUNT);
            double stdRatio = readDouble(paramsJsonMap.get("sor_std_ratio"), DEFAULT_SOR_STD_RATIO);
            return "SOR · k=" + neighborCount + " · std=" + stdRatio;
        }
        double radius = readDouble(paramsJsonMap.get("ror_radius"), DEFAULT_ROR_RADIUS);
        int minNeighbors = readInt(paramsJsonMap.get("ror_min_neighbors"), DEFAULT_ROR_MIN_NEIGHBORS);
        return "ROR · r=" + radius + " · minN=" + minNeighbors;
    }

    private static int readInt(Object rawValue, int defaultValue) {
        if (rawValue instanceof Number number) {
            return number.intValue();
        }
        return defaultValue;
    }

    private static double readDouble(Object rawValue, double defaultValue) {
        if (rawValue instanceof Number number) {
            return number.doubleValue();
        }
        return defaultValue;
    }
}
