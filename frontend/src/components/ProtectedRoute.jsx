import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useAuth } from 'contexts/AuthContext';
import Loader from 'components/Loader/Loader';

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loader />;
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <Outlet />;
}
