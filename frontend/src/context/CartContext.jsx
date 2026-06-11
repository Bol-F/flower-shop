import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import { getCart, addToCart, updateCartItem, removeFromCart, clearCart } from '../api/cart';
import { AuthContext } from './AuthContext';

export const CartContext = createContext(null);

export function CartProvider({ children }) {
  const { isAuthenticated } = useContext(AuthContext);
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null);
      return;
    }
    setLoading(true);
    try {
      const { data } = await getCart();
      setCart(data);
    } catch {
      setCart(null);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addItem = async (productId, quantity = 1) => {
    const { data } = await addToCart(productId, quantity);
    setCart(data);
  };

  const updateItem = async (productId, quantity) => {
    const { data } = await updateCartItem(productId, quantity);
    setCart(data);
  };

  const removeItem = async (productId) => {
    await removeFromCart(productId);
    await fetchCart();
  };

  const emptyCart = async () => {
    await clearCart();
    await fetchCart();
  };

  const value = {
    cart,
    loading,
    addItem,
    updateItem,
    removeItem,
    emptyCart,
    totalItems: cart?.total_items || 0,
    totalPrice: cart?.total_price || 0,
    refreshCart: fetchCart,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
