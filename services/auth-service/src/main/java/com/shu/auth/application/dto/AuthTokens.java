package com.shu.auth.application.dto;

public record AuthTokens(
        String accessToken,
        String refreshToken,
        long expiresIn) {
}
