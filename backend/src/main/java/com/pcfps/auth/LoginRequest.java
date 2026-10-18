package com.pcfps.auth;

import jakarta.validation.constraints.NotBlank;

/**
 * Login request body.
 *
 * @param username login name
 * @param password plain password
 * @author PCFPS
 * @date 2026-04-12
 */
public record LoginRequest(
        @NotBlank String username,
        @NotBlank String password
) {
}
