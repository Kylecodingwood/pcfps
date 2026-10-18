package com.pcfps.auth;

import com.pcfps.config.JwtProperties;
import com.pcfps.config.JwtService;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Authenticates users and issues JWTs.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final UserAccountRepository userAccountRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final JwtProperties jwtProperties;

    public AuthService(
            UserAccountRepository userAccountRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            JwtProperties jwtProperties
    ) {
        this.userAccountRepository = userAccountRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.jwtProperties = jwtProperties;
    }

    /**
     * Validates credentials and returns a new access token.
     *
     * @param loginRequest username and password from client
     * @return token envelope
     * @throws BadCredentialsException when user missing or password mismatch
     */
    @Transactional(readOnly = true)
    public LoginResponse login(LoginRequest loginRequest) {
        UserAccount userAccount = userAccountRepository.findByUsername(loginRequest.username())
                .orElseThrow(() -> {
                    log.warn("Login attempt for unknown username={}", loginRequest.username());
                    return new BadCredentialsException("Invalid username or password");
                });
        if (!userAccount.isEnabled()) {
            log.warn("Login attempt for disabled username={}", loginRequest.username());
            throw new BadCredentialsException("Invalid username or password");
        }
        if (!passwordEncoder.matches(loginRequest.password(), userAccount.getPasswordHash())) {
            log.warn("Login attempt bad password for username={}", loginRequest.username());
            throw new BadCredentialsException("Invalid username or password");
        }
        String token = jwtService.createToken(userAccount.getId(), userAccount.getUsername());
        long expiresSeconds = jwtProperties.expirationMs() / 1000L;
        log.info("User logged in username={} userId={}", userAccount.getUsername(), userAccount.getId());
        return new LoginResponse(token, expiresSeconds, userAccount.getUsername());
    }
}
