package com.shu.auth.presentation.dto;

import java.util.UUID;

public record RegisterResponse(
        UUID id,
        String email,
        String role) {
}
