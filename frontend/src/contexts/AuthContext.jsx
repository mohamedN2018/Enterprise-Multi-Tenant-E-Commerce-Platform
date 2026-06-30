import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';

import { apiGet, apiPost, tokenStore, storeHeader } from 'api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    if (!tokenStore.access) {
      setLoading(false);
      return;
    }
    try {
      setUser(await apiGet('/auth/me/'));
    } catch {
      tokenStore.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const login = useCallback(async (email, password) => {
    // data = { user, tokens: { access, refresh } }
    const result = await apiPost('/auth/login/', { email, password });
    tokenStore.set({ access: result.tokens.access, refresh: result.tokens.refresh });
    setUser(result.user);
    return result.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      if (tokenStore.refresh) await apiPost('/auth/logout/', { refresh: tokenStore.refresh });
    } catch {
      /* ignore */
    }
    tokenStore.clear();
    storeHeader.set('');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

AuthProvider.propTypes = { children: PropTypes.node };

export const useAuth = () => useContext(AuthContext);
