package com.shu.auth.presentation.dto;

public record RefreshResponse(
        String accessToken,
        String tokenType) {
}
