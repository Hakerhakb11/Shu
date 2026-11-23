import { useCallback, useEffect, useState } from 'react';
import { ApiError, catalogApi } from '../api/client';
import type { ModerationTargetStatus, PaginatedBooks } from '../types';

export function ModerationPage() {
  const [data, setData] = useState<PaginatedBooks | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await catalogApi.listModerationItems(page, 20);
      setData(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось загрузить очередь модерации');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const handleSetStatus = async (itemId: number, status: ModerationTargetStatus) => {
    setBusyId(itemId);
    setError(null);
    try {
      await catalogApi.updateItemStatus(itemId, status);
      await loadQueue();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось изменить статус');
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (itemId: number) => {
    setBusyId(itemId);
    setError(null);
    try {
      await catalogApi.deleteItem(itemId);
      await loadQueue();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Не удалось удалить товар');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section>
      <div className="page-header">
        <h1>Очередь модерации (PENDING)</h1>
        {data && <span className="muted">Ожидают проверки: {data.total}</span>}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p className="muted">Загрузка...</p>}

      {!loading && data && data.items.length === 0 && (
        <div className="card empty-state">
          <p>Все товары проверены — очередь модерации пуста.</p>
        </div>
      )}

      {!loading && data && data.items.length > 0 && (
        <div className="stack">
          {data.items.map((book) => {
            const busy = busyId === book.id;
            return (
              <div key={book.id} className="card moderation-row">
                <div>
                  <h3>
                    #{book.id} {book.title}
                  </h3>
                  <p className="book-author">{book.author}</p>
                  <p className="muted">
                    Цена: {book.price.toFixed(2)} ₽ · Остаток: {book.stock} · Продавец:{' '}
                    <code>{book.seller_id}</code>
                  </p>
                </div>

                <div className="inline-gap">
                  <button
                    className="btn btn-primary"
                    disabled={busy}
                    onClick={() => handleSetStatus(book.id, 'APPROVED')}
                  >
                    Одобрить
                  </button>
                  <button
                    className="btn btn-secondary"
                    disabled={busy}
                    onClick={() => handleSetStatus(book.id, 'REJECTED')}
                  >
                    Отклонить
                  </button>
                  <button
                    className="btn btn-danger"
                    disabled={busy}
                    onClick={() => handleSetStatus(book.id, 'BLOCKED')}
                  >
                    Заблокировать
                  </button>
                  <button
                    className="btn btn-danger-outline"
                    disabled={busy}
                    onClick={() => handleDelete(book.id)}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            );
          })}

          {data.pages > 1 && (
            <div className="pagination">
              <button
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Назад
              </button>
              <span>
                Страница {data.page} из {data.pages}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Вперёд
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}