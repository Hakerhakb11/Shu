package com.shu.auth.infrastructure.persistence;

import com.shu.auth.domain.model.RefreshSession;
import com.shu.auth.domain.repository.RefreshSessionRepository;
import com.shu.auth.infrastructure.persistence.mapper.RefreshSessionMapper;
import com.shu.auth.infrastructure.persistence.repository.RefreshSessionJpaRepository;
import org.springframework.stereotype.Component;
import java.util.Optional;

@Component
public class RefreshSessionRepositoryAdapter implements RefreshSessionRepository {
    private final RefreshSessionJpaRepository repository;
    public RefreshSessionRepositoryAdapter(RefreshSessionJpaRepository repository) { this.repository = repository; }

    @Override public Optional<RefreshSession> findActiveByHash(String tokenHash) {
        return repository.findByTokenHashAndRevokedFalse(tokenHash).map(RefreshSessionMapper::toDomain);
    }
    @Override public RefreshSession save(RefreshSession session) {
        return RefreshSessionMapper.toDomain(repository.save(RefreshSessionMapper.toEntity(session)));
    }
    @Override public void revoke(String tokenHash) {
        repository.findByTokenHashAndRevokedFalse(tokenHash).ifPresent(session -> {
            session.revoke();
            repository.save(session);
        });
    }
}
