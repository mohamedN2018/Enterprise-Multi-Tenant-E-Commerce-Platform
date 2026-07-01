import { lazy } from 'react';
import { createBrowserRouter } from 'react-router-dom';

// project import
import AdminLayout from 'layouts/AdminLayout';
import GuestLayout from 'layouts/GuestLayout';
import StoreLayout from 'layouts/StoreLayout';
import ProtectedRoute from 'components/ProtectedRoute';

// Storefront (public, customer-facing)
const Home = lazy(() => import('views/storefront/Home'));
const ProductsPage = lazy(() => import('views/storefront/Products'));
const StorePage = lazy(() => import('views/storefront/Store'));
const ProductPage = lazy(() => import('views/storefront/Product'));
const CartPage = lazy(() => import('views/storefront/Cart'));
const CheckoutPage = lazy(() => import('views/storefront/Checkout'));
const AccountPage = lazy(() => import('views/storefront/Account'));
const NotFound = lazy(() => import('views/storefront/NotFound'));

// Admin console (staff)
const Overview = lazy(() => import('views/dashboard/Overview'));
const ResourcePage = lazy(() => import('views/resource/ResourcePage'));
const ResourceDetail = lazy(() => import('views/resource/ResourceDetail'));

// Auth
const Login = lazy(() => import('views/auth/login'));
const Register = lazy(() => import('views/auth/register'));

// ==============================|| ROUTING RENDER ||============================== //

const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <StoreLayout />,
      children: [
        { index: true, element: <Home /> },
        { path: 'products', element: <ProductsPage /> },
        { path: 'store/:slug', element: <StorePage /> },
        { path: 'product/:id', element: <ProductPage /> },
        { path: 'cart', element: <CartPage /> },
        { path: 'checkout', element: <CheckoutPage /> },
        { path: 'account', element: <AccountPage /> },
        { path: '*', element: <NotFound /> }
      ]
    },
    {
      element: <ProtectedRoute />,
      children: [
        {
          path: '/admin',
          element: <AdminLayout />,
          children: [
            { index: true, element: <Overview /> },
            { path: 'r/:key', element: <ResourcePage /> },
            { path: 'r/:key/:id', element: <ResourceDetail /> }
          ]
        }
      ]
    },
    {
      path: '/',
      element: <GuestLayout />,
      children: [
        { path: 'login', element: <Login /> },
        { path: 'register', element: <Register /> }
      ]
    }
  ],
  { basename: import.meta.env.VITE_APP_BASE_NAME }
);

export default router;
