package com.pcfps.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * Binds {@code application.yml} property records.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Configuration
@EnableConfigurationProperties({JwtProperties.class, PcfpsProperties.class, PreviewProperties.class, MlRfSemanticProperties.class})
public class ConfigBeans {
}
