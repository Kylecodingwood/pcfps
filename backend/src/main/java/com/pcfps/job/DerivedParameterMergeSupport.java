package com.pcfps.job;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Merges {@link CreateDerivedTaskRequest} with defaults for Python {@code python_derived}.
 *
 * @author PCFPS
 * @date 2026-05-10
 */
public final class DerivedParameterMergeSupport {

    public static final double DEFAULT_CLUSTER_TOLERANCE = 0.5;
    public static final int DEFAULT_MIN_CLUSTER_POINTS = 50;
    public static final int DEFAULT_NORMAL_NEIGHBOR_COUNT = 30;
    public static final double DEFAULT_ANGLE_THRESHOLD_DEG = 30.0;
    public static final double DEFAULT_DISTANCE_THRESHOLD = 0.3;
    public static final int DEFAULT_MIN_REGION_POINTS = 100;
    public static final int DEFAULT_MAX_SEEDS = 50;
    public static final double DEFAULT_CELL_SIZE_M = 0.6;
    public static final int DEFAULT_MAX_WINDOW_SIZE = 8;
    public static final double DEFAULT_SLOPE_THRESHOLD = 0.15;
    public static final double DEFAULT_CLOTH_RESOLUTION = 0.5;
    public static final int DEFAULT_CSF_RIGIDNESS = 2;
    public static final int DEFAULT_CSF_ITERATIONS = 500;
    public static final double DEFAULT_CSF_CLASSIFY_THRESHOLD = 0.5;
    public static final double DEFAULT_SEMANTIC_PRUNE_GROUND_VOXEL_M = 0.5;

    private DerivedParameterMergeSupport() {
    }

    /**
     * @return merged params map and one-line summary for API
     */
    public static DerivedMergeResult mergeSegment(CreateDerivedTaskRequest request) {
        String algorithm = request.algorithm();
        if ("euclidean_cluster".equalsIgnoreCase(algorithm)) {
            double tolerance = request.clusterTolerance() != null
                    ? request.clusterTolerance()
                    : DEFAULT_CLUSTER_TOLERANCE;
            int minPoints = request.minClusterPoints() != null
                    ? request.minClusterPoints()
                    : DEFAULT_MIN_CLUSTER_POINTS;
            Integer maxPoints = request.maxClusterPoints();
            boolean useXyOnly = Boolean.TRUE.equals(request.useXyOnly());
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("cluster_tolerance", tolerance);
            map.put("min_cluster_points", minPoints);
            if (maxPoints != null) {
                map.put("max_cluster_points", maxPoints);
            }
            map.put("use_xy_only", useXyOnly);
            String summary = "分割·欧式 · tol=" + tolerance + " · minPts=" + minPoints;
            return new DerivedMergeResult(map, summary);
        }
        if ("region_growing".equalsIgnoreCase(algorithm)) {
            int normalK = request.normalNeighborCount() != null
                    ? request.normalNeighborCount()
                    : DEFAULT_NORMAL_NEIGHBOR_COUNT;
            double angleDeg = request.angleThresholdDeg() != null
                    ? request.angleThresholdDeg()
                    : DEFAULT_ANGLE_THRESHOLD_DEG;
            double dist = request.distanceThreshold() != null
                    ? request.distanceThreshold()
                    : DEFAULT_DISTANCE_THRESHOLD;
            int minRegion = request.minRegionPoints() != null
                    ? request.minRegionPoints()
                    : DEFAULT_MIN_REGION_POINTS;
            int maxSeeds = request.maxSeeds() != null ? request.maxSeeds() : DEFAULT_MAX_SEEDS;
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("normal_neighbor_count", normalK);
            map.put("angle_threshold_deg", angleDeg);
            map.put("distance_threshold", dist);
            map.put("min_region_points", minRegion);
            map.put("max_seeds", maxSeeds);
            String summary = "分割·区域生长 · k=" + normalK + " · ∠=" + angleDeg + "°";
            return new DerivedMergeResult(map, summary);
        }
        throw new IllegalArgumentException("Unknown segment algorithm: " + algorithm);
    }

    /**
     * Merges semantic-prune parameters for Python {@code semantic_prune} / {@code voxel_drop_ground}.
     *
     * @param request optional {@code groundVoxelSizeM}; defaults to {@link #DEFAULT_SEMANTIC_PRUNE_GROUND_VOXEL_M}
     * @return merged params (only {@code ground_voxel_size_m}; caller adds {@code semantic_legend_method})
     */
    public static DerivedMergeResult mergeSemanticPrune(CreateSemanticPruneTaskRequest request) {
        double voxelMeters = request.groundVoxelSizeM() != null
                ? request.groundVoxelSizeM()
                : DEFAULT_SEMANTIC_PRUNE_GROUND_VOXEL_M;
        if (!Double.isFinite(voxelMeters) || voxelMeters <= 0.0) {
            throw new IllegalArgumentException("groundVoxelSizeM must be a positive finite number");
        }
        Map<String, Object> parameterMap = new LinkedHashMap<>();
        parameterMap.put("ground_voxel_size_m", voxelMeters);
        String summaryLine = "语义精简·地面XY体素=" + voxelMeters + "m · 删3/4";
        return new DerivedMergeResult(parameterMap, summaryLine);
    }

    /**
     * @param request            derived create request
     * @param defaultMlRfModelDir configured default when request omits {@code mlRfModelDir}
     * @return merged params map and one-line summary for API
     */
    public static DerivedMergeResult mergeClassify(CreateDerivedTaskRequest request, String defaultMlRfModelDir) {
        String algorithm = request.algorithm();
        if ("pmf".equalsIgnoreCase(algorithm)) {
            double cell = request.cellSizeM() != null ? request.cellSizeM() : DEFAULT_CELL_SIZE_M;
            int win = request.maxWindowSize() != null ? request.maxWindowSize() : DEFAULT_MAX_WINDOW_SIZE;
            double slope = request.slopeThreshold() != null ? request.slopeThreshold() : DEFAULT_SLOPE_THRESHOLD;
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("cell_size_m", cell);
            map.put("max_window_size", win);
            map.put("slope_threshold", slope);
            String summary = "分类·PMF · cell=" + cell + "m · win=" + win;
            return new DerivedMergeResult(map, summary);
        }
        if ("csf".equalsIgnoreCase(algorithm)) {
            double res = request.clothResolution() != null ? request.clothResolution() : DEFAULT_CLOTH_RESOLUTION;
            int rigid = request.rigidness() != null ? request.rigidness() : DEFAULT_CSF_RIGIDNESS;
            int iterations = request.csfIterations() != null ? request.csfIterations() : DEFAULT_CSF_ITERATIONS;
            double threshold = request.classifyThreshold() != null
                    ? request.classifyThreshold()
                    : DEFAULT_CSF_CLASSIFY_THRESHOLD;
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("cloth_resolution", res);
            map.put("rigidness", rigid);
            map.put("iterations", iterations);
            map.put("classify_threshold", threshold);
            String summary = "分类·CSF · res=" + res + " · rigid=" + rigid;
            return new DerivedMergeResult(map, summary);
        }
        if ("rule_semantic_campus".equalsIgnoreCase(algorithm)) {
            double cell = request.cellSizeM() != null ? request.cellSizeM() : DEFAULT_CELL_SIZE_M;
            int win = request.maxWindowSize() != null ? request.maxWindowSize() : DEFAULT_MAX_WINDOW_SIZE;
            double slope = request.slopeThreshold() != null ? request.slopeThreshold() : DEFAULT_SLOPE_THRESHOLD;
            int neighborK = request.semanticNeighborCount() != null ? request.semanticNeighborCount() : 24;
            double planarityMax = request.semanticPlanarityBuildingMax() != null
                    ? request.semanticPlanarityBuildingMax()
                    : 0.12;
            double zStdVegMin = request.semanticZStdVegetationMin() != null
                    ? request.semanticZStdVegetationMin()
                    : 0.28;
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("cell_size_m", cell);
            map.put("max_window_size", win);
            map.put("slope_threshold", slope);
            map.put("semantic_neighbor_count", neighborK);
            map.put("semantic_planarity_building_max", planarityMax);
            map.put("semantic_z_std_vegetation_min", zStdVegMin);
            String summary = "分类·校园规则语义 · PMF地面 · k=" + neighborK;
            return new DerivedMergeResult(map, summary);
        }
        if ("ml_rf_semantic".equalsIgnoreCase(algorithm)) {
            String modelDirRaw = request.mlRfModelDir();
            if (modelDirRaw == null || modelDirRaw.isBlank()) {
                modelDirRaw = defaultMlRfModelDir;
            }
            if (modelDirRaw == null || modelDirRaw.isBlank()) {
                throw new IllegalArgumentException("ml_rf_semantic requires model_dir (request or pcfps.ml-rf-semantic.model-dir)");
            }
            Path modelDirectoryPath = Paths.get(modelDirRaw.trim()).normalize().toAbsolutePath();
            int neighborK = request.semanticNeighborCount() != null ? request.semanticNeighborCount() : 24;
            Map<String, Object> map = new LinkedHashMap<>();
            map.put("model_dir", modelDirectoryPath.toString());
            map.put("semantic_neighbor_count", neighborK);
            String summary = "分类·RF语义 · model=" + modelDirectoryPath.getFileName();
            return new DerivedMergeResult(map, summary);
        }
        throw new IllegalArgumentException("Unknown classify algorithm: " + algorithm);
    }

    /**
     * @param paramsJsonMap persisted derived params
     * @param derivedMethod algorithm token
     */
    public static String summarizePersistedSegment(String derivedMethod, Map<String, Object> paramsJsonMap) {
        if ("euclidean_cluster".equalsIgnoreCase(derivedMethod)) {
            double tolerance = readDouble(paramsJsonMap.get("cluster_tolerance"), DEFAULT_CLUSTER_TOLERANCE);
            int minPoints = readInt(paramsJsonMap.get("min_cluster_points"), DEFAULT_MIN_CLUSTER_POINTS);
            return "分割·欧式 · tol=" + tolerance + " · minPts=" + minPoints;
        }
        if ("region_growing".equalsIgnoreCase(derivedMethod)) {
            int normalK = readInt(paramsJsonMap.get("normal_neighbor_count"), DEFAULT_NORMAL_NEIGHBOR_COUNT);
            double angleDeg = readDouble(paramsJsonMap.get("angle_threshold_deg"), DEFAULT_ANGLE_THRESHOLD_DEG);
            return "分割·区域生长 · k=" + normalK + " · ∠=" + angleDeg + "°";
        }
        return "分割·" + derivedMethod;
    }

    public static String summarizePersistedClassify(String derivedMethod, Map<String, Object> paramsJsonMap) {
        if ("pmf".equalsIgnoreCase(derivedMethod)) {
            double cell = readDouble(paramsJsonMap.get("cell_size_m"), DEFAULT_CELL_SIZE_M);
            int win = readInt(paramsJsonMap.get("max_window_size"), DEFAULT_MAX_WINDOW_SIZE);
            return "分类·PMF · cell=" + cell + "m · win=" + win;
        }
        if ("csf".equalsIgnoreCase(derivedMethod)) {
            double res = readDouble(paramsJsonMap.get("cloth_resolution"), DEFAULT_CLOTH_RESOLUTION);
            int rigid = readInt(paramsJsonMap.get("rigidness"), DEFAULT_CSF_RIGIDNESS);
            return "分类·CSF · res=" + res + " · rigid=" + rigid;
        }
        if ("rule_semantic_campus".equalsIgnoreCase(derivedMethod)) {
            int neighborK = readInt(paramsJsonMap.get("semantic_neighbor_count"), 24);
            return "分类·校园规则语义 · k=" + neighborK;
        }
        if ("ml_rf_semantic".equalsIgnoreCase(derivedMethod)) {
            Object modelDirRaw = paramsJsonMap.get("model_dir");
            String modelDirLabel = modelDirRaw != null ? String.valueOf(modelDirRaw) : "default";
            return "分类·RF语义 · " + modelDirLabel;
        }
        return "分类·" + derivedMethod;
    }

    /**
     * One-line summary for a persisted {@link TaskKind#SEMANTIC_PRUNE} task.
     *
     * @param paramsJsonMap persisted derived params including {@code ground_voxel_size_m}
     * @return Chinese summary for job list
     */
    public static String summarizePersistedSemanticPrune(Map<String, Object> paramsJsonMap) {
        double voxelMeters = readDouble(paramsJsonMap.get("ground_voxel_size_m"), DEFAULT_SEMANTIC_PRUNE_GROUND_VOXEL_M);
        return "语义精简·地面XY体素=" + voxelMeters + "m · 删3/4";
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

    /**
     * @param mergedParams merged parameter map
     * @param summaryLine  one-line summary for DTO
     */
    public record DerivedMergeResult(Map<String, Object> mergedParams, String summaryLine) {
    }
}
