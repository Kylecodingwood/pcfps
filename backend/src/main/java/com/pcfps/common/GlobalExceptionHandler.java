package com.pcfps.common;

import com.pcfps.config.TraceIdFilter;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Maps exceptions to {@link ApiErrorResponse} and logs failures.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiErrorResponse> handleBusiness(BusinessException exception) {
        log.warn("Business error code={} message={}", exception.getCode(), exception.getMessage());
        HttpStatus status = mapBusinessCodeToStatus(exception.getCode());
        return ResponseEntity
                .status(status)
                .body(new ApiErrorResponse(exception.getCode(), exception.getMessage(), currentTraceId()));
    }

    private static HttpStatus mapBusinessCodeToStatus(String code) {
        if ("TASK_NOT_FOUND".equals(code) || "FILE_NOT_FOUND".equals(code)) {
            return HttpStatus.NOT_FOUND;
        }
        if ("PREVIEW_FILE_TOO_LARGE".equals(code)) {
            return HttpStatus.PAYLOAD_TOO_LARGE;
        }
        if ("LAS_PREVIEW_FAILED".equals(code)) {
            return HttpStatus.SERVICE_UNAVAILABLE;
        }
        if ("PREVIEW_PATH_INVALID".equals(code)) {
            return HttpStatus.BAD_REQUEST;
        }
        return HttpStatus.BAD_REQUEST;
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiErrorResponse> handleUnreadable(HttpMessageNotReadableException exception) {
        log.warn("Unreadable HTTP message: {}", exception.getMessage());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(new ApiErrorResponse("BAD_JSON", "Request body must be valid JSON", currentTraceId()));
    }

    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<ApiErrorResponse> handleBadCredentials(BadCredentialsException exception) {
        log.warn("Login failed: {}", exception.getMessage());
        return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .body(new ApiErrorResponse("AUTH_INVALID", "Invalid username or password", currentTraceId()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiErrorResponse> handleValidation(MethodArgumentNotValidException exception) {
        String message = exception.getBindingResult().getFieldErrors().stream()
                .findFirst()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .orElse("Validation failed");
        log.warn("Validation failed: {}", message);
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(new ApiErrorResponse("VALIDATION_ERROR", message, currentTraceId()));
    }

    @ExceptionHandler(ObjectOptimisticLockingFailureException.class)
    public ResponseEntity<ApiErrorResponse> handleOptimisticLock(ObjectOptimisticLockingFailureException exception) {
        log.error("Optimistic lock conflict: {}", exception.getMessage());
        return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(new ApiErrorResponse("CONCURRENT_UPDATE", "Resource was modified concurrently", currentTraceId()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiErrorResponse> handleGeneric(Exception exception) {
        log.error("Unhandled error: {}", exception.getMessage(), exception);
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new ApiErrorResponse("INTERNAL_ERROR", "Unexpected server error", currentTraceId()));
    }

    private static String currentTraceId() {
        String traceId = MDC.get(TraceIdFilter.TRACE_ID_MDC);
        return traceId != null ? traceId : "";
    }
}
