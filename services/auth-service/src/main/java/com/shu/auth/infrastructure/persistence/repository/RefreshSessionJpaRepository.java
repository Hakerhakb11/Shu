package com.shu.auth.infrastructure.persistence.repository;

import com.shu.auth.infrastructure.persistence.entity.RefreshSessionEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

public interface RefreshSessionJpaRepository extends JpaRepository<RefreshSessionEntity, UUID> {
    Optional<RefreshSessionEntity> findByTokenHashAndRevokedFalse(String tokenHash);
}
