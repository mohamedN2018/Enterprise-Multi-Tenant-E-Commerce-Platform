import { lazy } from 'react';
import { createBrowserRouter } from 'react-router-dom';

// project import
import AdminLayout from 'layouts/AdminLayout';
import GuestLayout from 'layouts/GuestLayout';
import ProtectedRoute from 'components/ProtectedRoute';

const Overview = lazy(() => import('views/dashboard/Overview'));
const ResourcePage = lazy(() => import('views/resource/ResourcePage'));
const Login = lazy(() => import('views/auth/login'));
const Register = lazy(() => import('views/auth/register'));

// ==============================|| ROUTING RENDER ||============================== //

const router = createBrowserRouter(
  [
    {
      element: <ProtectedRoute />,
      children: [
        {
          path: '/',
          element: <AdminLayout />,
          children: [
            { index: true, element: <Overview /> },
            { path: 'r/:key', element: <ResourcePage /> }
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
