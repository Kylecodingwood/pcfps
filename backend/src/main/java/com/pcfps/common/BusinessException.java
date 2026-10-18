package com.pcfps.common;

/**
 * Business rule or validation failure with a stable API error code.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
public class BusinessException extends RuntimeException {

    private final String code;

    public BusinessException(String code, String message) {
        super(message);
        this.code = code;
    }

    public String getCode() {
        return code;
    }
}
