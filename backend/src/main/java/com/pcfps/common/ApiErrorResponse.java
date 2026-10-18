package com.pcfps.common;

/**
 * Standard JSON error body for API failures.
 *
 * @param code    stable machine-readable code
 * @param message human-readable message
 * @param traceId correlation id from MDC
 * @author PCFPS
 * @date 2026-04-12
 */
public record ApiErrorResponse(String code, String message, String traceId) {
}
