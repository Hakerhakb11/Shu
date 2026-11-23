package com.shu.auth.infrastructure.persistence;

import com.shu.auth.domain.model.User;
import com.shu.auth.domain.repository.UserRepository;
import com.shu.auth.infrastructure.persistence.mapper.UserMapper;
import com.shu.auth.infrastructure.persistence.repository.UserJpaRepository;
import org.springframework.stereotype.Component;
import java.util.Optional;
import java.util.UUID;

@Component
public class UserRepositoryAdapter implements UserRepository {
    private final UserJpaRepository repository;
    public UserRepositoryAdapter(UserJpaRepository repository) { this.repository = repository; }

    @Override public Optional<User> findByEmail(String email) {
        return repository.findByEmail(email).map(UserMapper::toDomain);
    }
    @Override public Optional<User> findById(UUID id) {
        return repository.findById(id).map(UserMapper::toDomain);
    }
    @Override public User save(User user) {
        return UserMapper.toDomain(repository.save(UserMapper.toEntity(user)));
    }
}
