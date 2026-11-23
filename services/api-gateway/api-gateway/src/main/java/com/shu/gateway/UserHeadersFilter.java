package com.shu.gateway;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.security.core.context.ReactiveSecurityContextHolder;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.Collection;

/**
 * Убирает X-User-Id / X-User-Role, пришедшие от клиента (их можно подделать),
 * и выставляет свои значения из проверенного JWT.
 */
@Component
public class UserHeadersFilter implements GlobalFilter, Ordered {

    private static final String USER_ID = "X-User-Id";
    private static final String USER_ROLE = "X-User-Role";

    private final String roleClaim;

    public UserHeadersFilter(@Value("${gateway.jwt.role-claim:role}") String roleClaim) {
        this.roleClaim = roleClaim;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerWebExchange clean = exchange.mutate()
                .request(r -> r.headers(h -> {
                    h.remove(USER_ID);
                    h.remove(USER_ROLE);
                }))
                .build();

        return ReactiveSecurityContextHolder.getContext()
                .map(SecurityContext::getAuthentication)
                .filter(a -> a instanceof JwtAuthenticationToken)
                .cast(JwtAuthenticationToken.class)
                .map(a -> {
                    Jwt jwt = a.getToken();
                    String role = extractRole(jwt);
                    return clean.mutate()
                            .request(r -> r.headers(h -> {
                                h.set(USER_ID, jwt.getSubject());
                                if (role != null) {
                                    h.set(USER_ROLE, role);
                                }
                            }))
                            .build();
                })
                .defaultIfEmpty(clean)
                .flatMap(chain::filter);
    }

    private String extractRole(Jwt jwt) {
        Object raw = jwt.getClaim(roleClaim);
        if (raw instanceof Collection<?> c) {
            return c.stream().findFirst().map(Object::toString).orElse(null);
        }
        return raw != null ? raw.toString() : null;
    }

    @Override
    public int getOrder() {
        return 0;
    }
}
