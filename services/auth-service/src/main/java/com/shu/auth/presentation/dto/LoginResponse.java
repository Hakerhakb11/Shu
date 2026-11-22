package com.shu.auth.presentation.dto;

public record LoginResponse(
        String accessToken,
        String tokenType,
        long expiresIn) {
}
