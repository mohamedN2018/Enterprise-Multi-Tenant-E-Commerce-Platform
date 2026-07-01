import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Badge, Button, Card, Modal, Spinner, Table } from 'react-bootstrap';

import api, { errorMessage } from 'api/client';
import { onImgError, productImage } from 'utils/media';

const STATUS_VARIANT = { confirmed: 'success', completed: 'success', pending: 'warning', cancelled: 'danger' };

export default function OrdersTab({ store }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState(null);
  const [returning, setReturning] = useState(false);
  const [notice, setNotice] = useState('');
  const currency = store?.currency || '';
  const headers = { 'X-Store-Id': store.id };

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/orders/', { headers, params: { page_size: 50 } });
      setOrders(Array.isArray(res.data) ? res.data : res.data?.results || []);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.id]);

  useEffect(() => {
    load();
  }, [load]);

  const requestReturn = async () => {
    if (!detail || !window.confirm('Request a refund return for all items in this order?')) return;
    setReturning(true);
    setNotice('');
    try {
      await api.post(
        '/returns/',
        {
          order_id: detail.id,
          reason: 'Requested from account',
          resolution: 'refund',
          items: (detail.items || []).map((it) => ({ order_item_id: it.id, quantity: it.quantity }))
        },
        { headers }
      );
      setNotice('Return requested — the seller will review it.');
    } catch (e) {
      setNotice(errorMessage(e));
    } finally {
      setReturning(false);
    }
  };

  if (loading) return <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div>;
  if (error) return <Alert variant="danger">{error}</Alert>;
  if (orders.length === 0)
    return (
      <Alert variant="info">
        No orders yet. <Link to="/products">Start shopping →</Link>
      </Alert>
    );

  return (
    <>
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
            <tr key={o.id} style={{ cursor: 'pointer' }} onClick={() => { setDetail(o); setNotice(''); }}>
              <td className="fw-semibold">{o.number}</td>
              <td><Badge bg={STATUS_VARIANT[o.status] || 'secondary'}>{o.status}</Badge></td>
              <td>{o.items?.length ?? '—'}</td>
              <td className="text-end">{o.total} {o.currency}</td>
              <td>{o.created_at ? String(o.created_at).slice(0, 10) : '—'}</td>
              <td className="text-end text-muted">View →</td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Modal show={Boolean(detail)} onHide={() => setDetail(null)} centered>
        <Modal.Header closeButton>
          <Modal.Title className="h6">
            Order {detail?.number} <Badge bg={STATUS_VARIANT[detail?.status] || 'secondary'}>{detail?.status}</Badge>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {notice && <Alert variant="info" className="py-2">{notice}</Alert>}
          {(detail?.items || []).map((it) => (
            <div key={it.id} className="d-flex align-items-center gap-3 border-bottom py-2">
              <img src={productImage({ id: it.sku, slug: it.sku }, 100, 100)} alt="" className="thumb" onError={onImgError(it.sku)} />
              <div className="flex-grow-1">
                <div className="fw-semibold">{it.product_name}</div>
                <div className="small text-muted">{it.unit_price} {currency} × {it.quantity}</div>
              </div>
              <div className="fw-semibold">{it.line_total} {currency}</div>
            </div>
          ))}
          <div className="d-flex justify-content-between mt-3">
            <span className="text-muted">Total</span>
            <span className="h6 mb-0">{detail?.total} {detail?.currency}</span>
          </div>
        </Modal.Body>
        <Modal.Footer>
          {detail?.status === 'confirmed' && (
            <Button variant="outline-danger" size="sm" onClick={requestReturn} disabled={returning}>
              {returning ? <Spinner animation="border" size="sm" /> : 'Request return'}
            </Button>
          )}
          <Button variant="secondary" size="sm" onClick={() => setDetail(null)}>Close</Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}
