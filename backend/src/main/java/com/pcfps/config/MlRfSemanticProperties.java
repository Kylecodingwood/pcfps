package com.pcfps.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Default RandomForest semantic model directory for {@code ml_rf_semantic} derived jobs.
 *
 * @param modelDir absolute or resolvable path containing {@code model.joblib} and {@code feature_config.json}
 * @author PCFPS
 * @date 2026-05-15
 */
@ConfigurationProperties(prefix = "pcfps.ml-rf-semantic")
public record MlRfSemanticProperties(String modelDir) {
}
