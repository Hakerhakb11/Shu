package com.shu.auth.infrastructure.persistence.mapper;

import com.shu.auth.domain.model.User;
import com.shu.auth.infrastructure.persistence.entity.UserEntity;

public final class UserMapper {
    private UserMapper() {}
    public static User toDomain(UserEntity entity) {
        return new User(
                entity.getId(),
                entity.getEmail(),
                entity.getPasswordHash(),
                entity.getRole());
    }

    public static UserEntity toEntity(User user) {
        return new UserEntity(
                user.id(),
                user.email(),
                user.passwordHash(),
                user.role());
    }
}
