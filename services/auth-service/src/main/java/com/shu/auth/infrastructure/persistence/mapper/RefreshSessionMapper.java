package com.shu.auth.infrastructure.persistence.mapper;

import com.shu.auth.domain.model.RefreshSession;
import com.shu.auth.infrastructure.persistence.entity.RefreshSessionEntity;

public final class RefreshSessionMapper {
    private RefreshSessionMapper() {}

    public static RefreshSession toDomain(RefreshSessionEntity entity) {
        return new RefreshSession(
                entity.getId(),
                entity.getUserId(),
                entity.getTokenHash(),
                entity.getExpiresAt(),
                entity.isRevoked());
    }

    public static RefreshSessionEntity toEntity(RefreshSession session) {
        return new RefreshSessionEntity(
                session.id(),
                session.userId(),
                session.tokenHash(),
                session.expiresAt(),
                session.revoked());
    }
}
