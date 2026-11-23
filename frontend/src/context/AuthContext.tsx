import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  authApi,
  decodeUserFromJwt,
  refreshAccessToken,
  setAccessToken,
  subscribeTokenChanges,
} from '../api/client';
import type { AuthUser, RegisterRole } from '../types';

interface AuthContextValue {
  user: AuthUser | null;
  isRestoring: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, role: RegisterRole) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [savedEmail, setSavedEmail] = useState<string | undefined>(undefined);
  const [isRestoring, setIsRestoring] = useState(true);

  useEffect(() => {
    const unsubscribe = subscribeTokenChanges((token) => {
      if (!token) {
        setUser(null);
      } else {
        setUser((prev) => decodeUserFromJwt(token, prev?.email ?? savedEmail));
      }
    });

    refreshAccessToken()
      .then((token) => {
        if (token) {
          setUser(decodeUserFromJwt(token));
        }
      })
      .finally(() => setIsRestoring(false));

    return unsubscribe;
  }, [savedEmail]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    setSavedEmail(email);
    setAccessToken(data.accessToken);
    setUser(decodeUserFromJwt(data.accessToken, email));
  }, []);

  const register = useCallback(
    async (email: string, password: string, role: RegisterRole) => {
      await authApi.register(email, password, role);
      await login(email, password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Даже если сервер вернул ошибку, очищаем клиентскую сессию
    } finally {
      setSavedEmail(undefined);
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, isRestoring, login, register, logout }),
    [user, isRestoring, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth должен использоваться внутри AuthProvider');
  return ctx;
}