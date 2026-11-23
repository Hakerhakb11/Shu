import { useCallback, useEffect, useState } from 'react';
import { cartApi } from './api/client';
import { useAuth } from './context/AuthContext';
import { AuthPage } from './pages/AuthPage';
import { CartPage } from './pages/CartPage';
import { CatalogPage } from './pages/CatalogPage';
import { ModerationPage } from './pages/ModerationPage';
import { SellerPage } from './pages/SellerPage';

type View = 'catalog' | 'cart' | 'seller' | 'moderation' | 'auth';

export function App() {
  const { user, isRestoring, logout } = useAuth();
  const [view, setView] = useState<View>('catalog');
  const [cartCount, setCartCount] = useState(0);

  const refreshCartCount = useCallback(async () => {
    if (!user) {
      setCartCount(0);
      return;
    }
    try {
      const cart = await cartApi.getCart();
      const totalQty = cart.items.reduce((acc, item) => acc + item.quantity, 0);
      setCartCount(totalQty);
    } catch {
      // Корзина может быть временно недоступна
    }
  }, [user]);

  useEffect(() => {
    refreshCartCount();
  }, [refreshCartCount]);

  const handleLogout = async () => {
    await logout();
    setCartCount(0);
    setView('catalog');
  };

  return (
    <div className="app-shell">
      <header className="navbar">
        <div className="container navbar-inner">
          <button className="brand" onClick={() => setView('catalog')}>
            Shu <span>Книги</span>
          </button>

          <nav className="nav-links">
            <button
              className={`nav-btn ${view === 'catalog' ? 'active' : ''}`}
              onClick={() => setView('catalog')}
            >
              Каталог
            </button>

            {user && (
              <button
                className={`nav-btn ${view === 'cart' ? 'active' : ''}`}
                onClick={() => setView('cart')}
              >
                Корзина {cartCount > 0 && <span className="pill">{cartCount}</span>}
              </button>
            )}

            {user?.role === 'SELLER' && (
              <button
                className={`nav-btn ${view === 'seller' ? 'active' : ''}`}
                onClick={() => setView('seller')}
              >
                Мои товары
              </button>
            )}

            {user?.role === 'MODERATOR' && (
              <button
                className={`nav-btn ${view === 'moderation' ? 'active' : ''}`}
                onClick={() => setView('moderation')}
              >
                Модерация
              </button>
            )}
          </nav>

          <div className="nav-user">
            {isRestoring ? (
              <span className="muted">Проверка сессии...</span>
            ) : user ? (
              <>
                <span className="role-chip">{user.role}</span>
                <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
                  Выйти
                </button>
              </>
            ) : (
              <button className="btn btn-primary btn-sm" onClick={() => setView('auth')}>
                Войти
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="container main-content">
        {view === 'catalog' && (
          <CatalogPage
            onCartChanged={refreshCartCount}
            onRequireAuth={() => setView('auth')}
          />
        )}
        {view === 'cart' &&
          (user ? (
            <CartPage
              onCartChanged={refreshCartCount}
              onGoToCatalog={() => setView('catalog')}
            />
          ) : (
            <AuthPage onSuccess={() => setView('cart')} />
          ))}
        {view === 'seller' &&
          (user?.role === 'SELLER' ? (
            <SellerPage />
          ) : (
            <div className="alert alert-error">Раздел доступен только продавцам (SELLER).</div>
          ))}
        {view === 'moderation' &&
          (user?.role === 'MODERATOR' ? (
            <ModerationPage />
          ) : (
            <div className="alert alert-error">Раздел доступен только модераторам (MODERATOR).</div>
          ))}
        {view === 'auth' && <AuthPage onSuccess={() => setView('catalog')} />}
      </main>
    </div>
  );
}