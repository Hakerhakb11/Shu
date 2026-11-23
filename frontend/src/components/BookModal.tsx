import { useEffect, useState } from 'react';
import { ApiError, catalogApi } from '../api/client';
import type { BookDetail } from '../types';

interface BookModalProps {
  bookId: number;
  onClose: () => void;
  onAddToCart: (bookId: number) => Promise<void>;
  canAddToCart: boolean;
}

export function BookModal({ bookId, onClose, onAddToCart, canAddToCart }: BookModalProps) {
  const [book, setBook] = useState<BookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    catalogApi
      .getItem(bookId)
      .then(setBook)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Не удалось загрузить книгу'))
      .finally(() => setLoading(false));
  }, [bookId]);

  const handleAdd = async () => {
    setAdding(true);
    try {
      await onAddToCart(bookId);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Закрыть">
          ×
        </button>

        {loading && <p className="muted">Загрузка карточки книги...</p>}
        {error && <div className="alert alert-error">{error}</div>}

        {book && (
          <div className="book-detail">
            <div className="book-detail-cover">
              {book.image_url ? (
                <img src={book.image_url} alt={book.title} />
              ) : (
                <div className="cover-placeholder">Нет обложки</div>
              )}
            </div>

            <div className="book-detail-info">
              <span className="badge">{book.category?.name ?? `Категория #${book.category_id}`}</span>
              <h2>{book.title}</h2>
              <p className="book-author">{book.author}</p>
              <p className="book-price-lg">{book.price.toFixed(2)} ₽</p>
              <p className="muted">Остаток на складе: {book.stock} шт.</p>

              <p className="book-description">{book.description}</p>

              {book.characteristics.length > 0 && (
                <div className="characteristics">
                  <h4>Характеристики</h4>
                  <dl>
                    {book.characteristics.map((ch, idx) => (
                      <div key={ch.id ?? idx} className="char-row">
                        <dt>{ch.name}</dt>
                        <dd>{ch.value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}

              <div className="modal-actions">
                <button
                  className="btn btn-primary"
                  disabled={!canAddToCart || book.stock <= 0 || adding}
                  onClick={handleAdd}
                >
                  {book.stock <= 0
                    ? 'Нет в наличии'
                    : !canAddToCart
                      ? 'Войдите, чтобы добавить в корзину'
                      : adding
                        ? 'Добавление...'
                        : 'В корзину'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}