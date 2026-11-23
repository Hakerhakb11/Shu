"""Фабрика асинхронного клиента Redis."""

from redis.asyncio import Redis


def create_redis_client(redis_url: str, socket_timeout: float = 3.0) -> Redis:
    """Создать асинхронный клиент Redis с декодированием строк."""
    return Redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_timeout,
    )
