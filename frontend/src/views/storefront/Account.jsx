import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Badge, Button, Card, Modal, Spinner, Table } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';
import { onImgError, productImage } from 'utils/media';

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
  const [detail, setDetail] = useState(null);

  const currency = shopStore?.currency || '';

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
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id} style={{ cursor: 'pointer' }} onClick={() => setDetail(o)}>
                    <td className="fw-semibold">{o.number}</td>
                    <td>
                      <Badge bg={STATUS_VARIANT[o.status] || 'secondary'}>{o.status}</Badge>
                    </td>
                    <td>{o.items?.length ?? '—'}</td>
                    <td className="text-end">
                      {o.total} {o.currency}
                    </td>
                    <td>{o.created_at ? String(o.created_at).slice(0, 10) : '—'}</td>
                    <td className="text-end">
                      <FeatherIcon icon="chevron-right" size={16} className="text-muted" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}

      <Modal show={Boolean(detail)} onHide={() => setDetail(null)} centered>
        <Modal.Header closeButton>
          <Modal.Title className="h6">
            Order {detail?.number}{' '}
            <Badge bg={STATUS_VARIANT[detail?.status] || 'secondary'}>{detail?.status}</Badge>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {(detail?.items || []).map((it) => (
            <div key={it.id} className="d-flex align-items-center gap-3 border-bottom py-2">
              <img src={productImage({ id: it.sku, slug: it.sku }, 100, 100)} alt="" className="thumb" onError={onImgError(it.sku)} />
              <div className="flex-grow-1">
                <div className="fw-semibold">{it.product_name}</div>
                <div className="small text-muted">
                  {it.unit_price} {currency} × {it.quantity}
                </div>
              </div>
              <div className="fw-semibold">
                {it.line_total} {currency}
              </div>
            </div>
          ))}
          <div className="d-flex justify-content-between mt-3">
            <span className="text-muted">Total</span>
            <span className="h6 mb-0">
              {detail?.total} {detail?.currency}
            </span>
          </div>
        </Modal.Body>
      </Modal>
    </>
  );
}
