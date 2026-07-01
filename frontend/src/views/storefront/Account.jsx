import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Badge, Card, Spinner, Table } from 'react-bootstrap';

import api, { errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';

const STATUS_VARIANT = {
  confirmed: 'success',
  completed: 'success',
  pending: 'warning',
  cancelled: 'danger'
};

export default function Account() {
  const { isAuthenticated, user } = useAuth();
  const { shopStore } = useCart();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!shopStore) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/orders/', {
        headers: { 'X-Store-Id': shopStore.id },
        params: { page_size: 50 }
      });
      setOrders(Array.isArray(res.data) ? res.data : res.data?.results || []);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [shopStore]);

  useEffect(() => {
    load();
  }, [load]);

  if (!isAuthenticated) {
    return (
      <Alert variant="info">
        Please <Link to="/login">sign in</Link> to see your orders.
      </Alert>
    );
  }

  return (
    <>
      <h3 className="fw-bold mb-1">My orders</h3>
      <p className="text-muted small">{user?.email}</p>
      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : !shopStore ? (
        <Alert variant="info">
          Start shopping to place your first order. <Link to="/">Browse stores →</Link>
        </Alert>
      ) : orders.length === 0 ? (
        <Alert variant="info">
          No orders yet at {shopStore.name}. <Link to={`/store/${shopStore.slug}`}>Shop now →</Link>
        </Alert>
      ) : (
        <Card className="border-0 shadow-sm">
          <Card.Body>
            <Table responsive hover className="align-middle mb-0">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Status</th>
                  <th>Items</th>
                  <th className="text-end">Total</th>
                  <th>Placed</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td className="fw-semibold">{o.number}</td>
                    <td>
                      <Badge bg={STATUS_VARIANT[o.status] || 'secondary'}>{o.status}</Badge>
                    </td>
                    <td>{o.items?.length ?? '—'}</td>
                    <td className="text-end">
                      {o.total} {o.currency}
                    </td>
                    <td>{o.created_at ? String(o.created_at).slice(0, 10) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
    </>
  );
}
