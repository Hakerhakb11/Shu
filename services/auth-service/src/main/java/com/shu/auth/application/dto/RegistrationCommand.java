package com.shu.auth.application.dto;

import com.shu.auth.domain.model.Role;

public record RegistrationCommand(
        String email,
        String password,
        Role role) {
}
