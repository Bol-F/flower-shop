import React from 'react';
import { Routes, Route } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';

import HomePage from '../pages/HomePage';
import ProductsPage from '../pages/ProductsPage';
import ProductDetailPage from '../pages/ProductDetailPage';
import CartPage from '../pages/CartPage';
import CheckoutPage from '../pages/CheckoutPage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import ProfilePage from '../pages/ProfilePage';
import OrderHistoryPage from '../pages/OrderHistoryPage';
import AdminDashboard from '../pages/AdminDashboard';

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/products" element={<ProductsPage />} />
      <Route path="/products/:slug" element={<ProductDetailPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route path="/cart" element={
        <ProtectedRoute><CartPage /></ProtectedRoute>
      } />
      <Route path="/checkout" element={
        <ProtectedRoute><CheckoutPage /></ProtectedRoute>
      } />
      <Route path="/orders" element={
        <ProtectedRoute><OrderHistoryPage /></ProtectedRoute>
      } />
      <Route path="/orders/:id" element={
        <ProtectedRoute><OrderHistoryPage /></ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute><ProfilePage /></ProtectedRoute>
      } />
      <Route path="/admin" element={
        <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
      } />
    </Routes>
  );
}

export default AppRoutes;
