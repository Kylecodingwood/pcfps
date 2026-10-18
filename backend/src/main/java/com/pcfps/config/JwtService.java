package com.pcfps.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;

import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;

/**
 * Creates and parses Bearer JWTs for API access.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Service
public class JwtService {

    private final JwtProperties jwtProperties;
    private final SecretKey secretKey;

    public JwtService(JwtProperties jwtProperties) {
        this.jwtProperties = jwtProperties;
        this.secretKey = Keys.hmacShaKeyFor(jwtProperties.secret().getBytes(StandardCharsets.UTF_8));
    }

    /**
     * Builds a signed JWT for the given user.
     *
     * @param userId   subject user id
     * @param username claim for debugging
     * @return compact JWT string
     */
    public String createToken(UUID userId, String username) {
        long now = System.currentTimeMillis();
        Date expiry = new Date(now + jwtProperties.expirationMs());
        return Jwts.builder()
                .subject(userId.toString())
                .claim("username", username)
                .issuedAt(new Date(now))
                .expiration(expiry)
                .signWith(secretKey)
                .compact();
    }

    /**
     * Parses the user id from a valid token.
     *
     * @param token raw JWT (no Bearer prefix)
     * @return user id from subject claim
     */
    public UUID parseUserId(String token) {
        Claims claims = Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
        return UUID.fromString(claims.getSubject());
    }
}
