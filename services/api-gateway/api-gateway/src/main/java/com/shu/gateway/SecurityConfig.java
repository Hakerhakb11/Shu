package com.shu.gateway;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.oauth2.server.resource.web.server.authentication.ServerBearerTokenAuthenticationConverter;
import org.springframework.security.web.server.SecurityWebFilterChain;
import reactor.core.publisher.Mono;

/**
 * Gateway только проверяет, что запрос от залогиненного пользователя.
 * Проверку ролей (SELLER, MODERATOR) делают сами сервисы по X-User-Role.
 */
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Bean
    SecurityWebFilterChain securityFilterChain(ServerHttpSecurity http) {
        var bearer = new ServerBearerTokenAuthenticationConverter();

        return http
                .csrf(ServerHttpSecurity.CsrfSpec::disable)
                .authorizeExchange(ex -> ex
                        .pathMatchers(HttpMethod.OPTIONS).permitAll()
                        .pathMatchers("/actuator/health/**").permitAll()
                        // auth-service сам работает с токенами (login, refresh, logout)
                        .pathMatchers("/auth/**").permitAll()
                        // только для cart-service, снаружи недоступно
                        .pathMatchers(HttpMethod.POST, "/catalog/items/batch").denyAll()
                        // публичное чтение каталога
                        .pathMatchers(HttpMethod.GET,
                                "/catalog/items", "/catalog/items/*", "/catalog/categories").permitAll()
                        // всё остальное: корзина, создание/правка товаров, модерация
                        .anyExchange().authenticated())
                .oauth2ResourceServer(o -> o
                        // на /auth/** токен не проверяем: logout должен работать и с просроченным токеном
                        .bearerTokenConverter(exchange ->
                                exchange.getRequest().getPath().value().startsWith("/auth/")
                                        ? Mono.empty()
                                        : bearer.convert(exchange))
                        .jwt(Customizer.withDefaults()))
                .build();
    }
}
