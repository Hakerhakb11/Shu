package com.shu.auth.presentation.mapper;

import com.shu.auth.application.dto.RegisteredUser;
import com.shu.auth.presentation.dto.RegisterResponse;

public final class AuthPresentationMapper {
    private AuthPresentationMapper() {}
    public static RegisterResponse toResponse(RegisteredUser user) {
        return new RegisterResponse(
                user.id(),
                user.email(),
                user.role().name());
    }
}
