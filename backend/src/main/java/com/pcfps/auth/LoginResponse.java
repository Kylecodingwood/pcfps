package com.pcfps.auth;

/**
 * Successful login payload with JWT.
 *
 * @param token             Bearer token value
 * @param expiresInSeconds  token TTL in seconds
 * @param username          authenticated username
 * @author PCFPS
 * @date 2026-04-12
 */
public record LoginResponse(String token, long expiresInSeconds, String username) {
}
