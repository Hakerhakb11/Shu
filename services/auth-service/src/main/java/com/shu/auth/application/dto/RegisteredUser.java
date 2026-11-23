package com.shu.auth.application.dto;

import com.shu.auth.domain.model.Role;
import java.util.UUID;

public record RegisteredUser(
        UUID id,
        String email,
        Role role) {
}
