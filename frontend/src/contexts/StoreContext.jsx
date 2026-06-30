import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';

import { apiGet, storeHeader } from 'api/client';
import { useAuth } from 'contexts/AuthContext';

const StoreContext = createContext(null);

export function StoreProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [stores, setStores] = useState([]);
  const [activeId, setActiveId] = useState(storeHeader.id);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const list = await apiGet('/stores/');
      const items = Array.isArray(list) ? list : list?.results || [];
      setStores(items);
      // Pick a sensible active store if none chosen (or the chosen one vanished).
      const stillValid = items.some((s) => s.id === storeHeader.id);
      if (items.length && !stillValid) {
        storeHeader.set(items[0].id);
        setActiveId(items[0].id);
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const selectStore = useCallback((id) => {
    storeHeader.set(id);
    setActiveId(id);
  }, []);

  const activeStore = stores.find((s) => s.id === activeId) || null;

  return (
    <StoreContext.Provider value={{ stores, activeStore, activeId, loading, selectStore, refresh }}>
      {children}
    </StoreContext.Provider>
  );
}

StoreProvider.propTypes = { children: PropTypes.node };

export const useStore = () => useContext(StoreContext);
