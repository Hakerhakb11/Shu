package com.shu.auth.domain.repository;

import com.shu.auth.domain.model.RefreshSession;
import java.util.Optional;

public interface RefreshSessionRepository {
    Optional<RefreshSession> findActiveByHash(String tokenHash);
    RefreshSession save(RefreshSession session);
    void revoke(String tokenHash);
}
