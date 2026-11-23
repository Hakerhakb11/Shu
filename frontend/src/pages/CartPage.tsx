import { useCallback, useEffect, useState } from 'react';
import { ApiError, cartApi } from '../api/client';
import type { CartResponse } from '../types';

interface CartPageProps {
  onCartChanged: () => void;
  onGoToCatalog: () => void;
}

export function CartPage({ onCartChanged, onGoToCatalog }: CartPageProps) {
  const [cart, setCart] = useState<CartResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyItemId, setBusyItemId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCart = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await cartApi.getCart();
      setCart(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить корзину');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCart();
  }, [loadCart]);

  const handleIncrement = async (itemId: number) => {
    setBusyItemId(itemId);
    setError(null);
    try {
      await cartApi.addItem(itemId, 1);
      await loadCart();
      onCartChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось увеличить количество');
    } finally {
      setBusyItemId(null);
    }
  };

  const handleDecrement = async (itemId: number) => {
    setBusyItemId(itemId);
    setError(null);
    try {
      await cartApi.removeItem(itemId, 1);
      await loadCart();
      onCartChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось уменьшить количество');
    } finally {
      setBusyItemId(null);
    }
  };

  const handleRemove = async (itemId: number) => {
    setBusyItemId(itemId);
    setError(null);
    try {
      await cartApi.removeItem(itemId);
      await loadCart();
      onCartChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось удалить позицию');
    } finally {
      setBusyItemId(null);
    }
  };

  const handleClear = async () => {
    setError(null);
    try {
      await cartApi.clearCart();
      await loadCart();
      onCartChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось очистить корзину');
    }
  };

  return (
    <section>
      <div className="page-header">
        <h1>Корзина</h1>
        {cart && cart.items.length > 0 && (
          <button className="btn btn-danger" onClick={handleClear}>
            Очистить корзину
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p className="muted">Загрузка корзины...</p>}

      {!loading && cart && cart.items.length === 0 && (
        <div className="card empty-state">
          <p>Ваша корзина пуста.</p>
          <button className="btn btn-primary" onClick={onGoToCatalog}>
            Перейти в каталог
          </button>
        </div>
      )}

      {!loading && cart && cart.items.length > 0 && (
        <>
          {cart.has_unavailable_items && (
            <div className="alert alert-warning">
              В корзине есть недоступные позиции — они не входят в итоговую сумму. Удалите их или
              уменьшите количество.
            </div>
          )}

          <div className="cart-list">
            {cart.items.map((item) => {
              const busy = busyItemId === item.item_id;
              return (
                <div
                  key={item.item_id}
                  className={`card cart-row ${!item.available ? 'cart-row-unavailable' : ''}`}
                >
                  <div className="cart-thumb">
                    {item.image_url ? (
                      <img src={item.image_url} alt={item.title ?? `Товар #${item.item_id}`} />
                    ) : (
                      <div className="cover-placeholder sm">#{item.item_id}</div>
                    )}
                  </div>

                  <div className="cart-info">
                    <h3>{item.title ?? `Книга #${item.item_id}`}</h3>
                    {item.author && <p className="book-author">{item.author}</p>}
                    {item.price !== null && (
                      <p className="muted">
                        Цена: {item.price.toFixed(2)} ₽
                        {item.stock !== null ? ` · В наличии: ${item.stock} шт.` : ''}
                      </p>
                    )}
                    {!item.available && (
                      <p className="unavailable-badge">
                        {item.message || 'Товар недоступен'}
                        {item.unavailable_reason ? ` (${item.unavailable_reason})` : ''}
                      </p>
                    )}
                  </div>

                  <div className="cart-controls">
                    <div className="qty-group">
                      <button
                        className="btn btn-secondary"
                        disabled={busy}
                        onClick={() => handleDecrement(item.item_id)}
                      >
                        −
                      </button>
                      <span className="qty-value">{item.quantity}</span>
                      <button
                        className="btn btn-secondary"
                        disabled={busy || !item.available}
                        onClick={() => handleIncrement(item.item_id)}
                      >
                        +
                      </button>
                    </div>

                    <div className="cart-line-total">{item.line_total.toFixed(2)} ₽</div>

                    <button
                      className="btn btn-danger-outline"
                      disabled={busy}
                      onClick={() => handleRemove(item.item_id)}
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="card cart-summary">
            <div>
              <span className="muted">Итого к оплате (только доступные товары):</span>
              <div className="book-price-lg">{cart.total_price.toFixed(2)} ₽</div>
            </div>
            <button
              className="btn btn-primary"
              disabled={cart.total_price <= 0}
              onClick={handleClear}
              title="Оформление заказа в MVP завершается очисткой корзины"
            >
              Оформить заказ (MVP)
            </button>
          </div>
        </>
      )}
    </section>
  );
}