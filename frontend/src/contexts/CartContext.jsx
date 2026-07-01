import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';

import api from 'api/client';
import { useAuth } from 'contexts/AuthContext';

// Storefront cart: server-side cart scoped to the store currently being shopped
// (checkout is per-store). The shopping store is persisted and sent explicitly
// as X-Store-Id on every cart call, independent of the admin's active store.

const CartContext = createContext(null);
const SHOP_KEY = 'shop_store';

const loadShop = () => {
  try {
    return JSON.parse(localStorage.getItem(SHOP_KEY) || 'null');
  } catch {
    return null;
  }
};

export function CartProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [shopStore, setShop] = useState(loadShop);
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);

  const headers = useMemo(() => (shopStore ? { 'X-Store-Id': shopStore.id } : {}), [shopStore]);

  const setShopStore = useCallback((store) => {
    const slim = store
      ? { id: store.id, slug: store.slug, name: store.name, currency: store.currency }
      : null;
    if (slim) localStorage.setItem(SHOP_KEY, JSON.stringify(slim));
    else localStorage.removeItem(SHOP_KEY);
    setShop(slim);
  }, []);

  const refreshCart = useCallback(async () => {
    if (!isAuthenticated || !shopStore) {
      setCart(null);
      return;
    }
    setLoading(true);
    try {
      const res = await api.get('/cart/', { headers: { 'X-Store-Id': shopStore.id } });
      setCart(res.data);
    } catch {
      setCart(null);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, shopStore]);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const addItem = useCallback(
    async (variantId, quantity = 1) => {
      if (!shopStore) throw new Error('Pick a store first.');
      await api.post(
        '/cart/items/',
        { variant_id: variantId, quantity },
        { headers: { 'X-Store-Id': shopStore.id } }
      );
      await refreshCart();
    },
    [shopStore, refreshCart]
  );

  const updateItem = useCallback(
    async (itemId, quantity) => {
      await api.patch(`/cart/items/${itemId}/`, { quantity }, { headers });
      await refreshCart();
    },
    [headers, refreshCart]
  );

  const removeItem = useCallback(
    async (itemId) => {
      await api.delete(`/cart/items/${itemId}/`, { headers });
      await refreshCart();
    },
    [headers, refreshCart]
  );

  const applyCoupon = useCallback(
    async (code) => {
      await api.post('/cart/coupon/', { code }, { headers });
      await refreshCart();
    },
    [headers, refreshCart]
  );

  const removeCoupon = useCallback(async () => {
    await api.delete('/cart/coupon/', { headers });
    await refreshCart();
  }, [headers, refreshCart]);

  const checkout = useCallback(
    async (options = {}) => {
      const res = await api.post('/cart/checkout/', options, { headers });
      await refreshCart();
      return res.data; // the created order
    },
    [headers, refreshCart]
  );

  const count = cart?.item_count || 0;

  const value = useMemo(
    () => ({
      shopStore,
      setShopStore,
      cart,
      count,
      loading,
      refreshCart,
      addItem,
      updateItem,
      removeItem,
      applyCoupon,
      removeCoupon,
      checkout
    }),
    [shopStore, setShopStore, cart, count, loading, refreshCart, addItem, updateItem, removeItem, applyCoupon, removeCoupon, checkout]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

CartProvider.propTypes = { children: PropTypes.node };

export const useCart = () => useContext(CartContext);
