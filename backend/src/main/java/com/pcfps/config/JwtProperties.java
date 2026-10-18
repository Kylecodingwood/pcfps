package com.pcfps.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * JWT signing configuration.
 *
 * @param secret       HMAC secret (use env JWT_SECRET in production)
 * @param expirationMs access token lifetime in milliseconds
 * @author PCFPS
 * @date 2026-04-12
 */
@ConfigurationProperties(prefix = "app.jwt")
public record JwtProperties(String secret, long expirationMs) {
}
