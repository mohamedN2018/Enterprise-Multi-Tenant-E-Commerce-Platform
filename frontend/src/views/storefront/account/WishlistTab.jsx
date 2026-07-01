import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Col, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { errorMessage } from 'api/client';
import { useCart } from 'contexts/CartContext';
import { onImgError, productImage } from 'utils/media';

export default function WishlistTab({ store }) {
  const { refreshCart } = useCart();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState('');
  const currency = store?.currency || '';
  const headers = { 'X-Store-Id': store.id };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/wishlist/', { headers });
      setItems(Array.isArray(res.data) ? res.data : res.data?.results || []);
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

  const remove = async (id) => {
    setBusyId(id);
    try {
      await api.delete(`/wishlist/${id}/`, { headers });
      load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyId('');
    }
  };

  const moveToCart = async (id) => {
    setBusyId(id);
    try {
      await api.post(`/wishlist/${id}/move-to-cart/`, { quantity: 1 }, { headers });
      await refreshCart();
      load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyId('');
    }
  };

  if (loading) return <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div>;

  return (
    <>
      {error && <Alert variant="danger">{error}</Alert>}
      {items.length === 0 ? (
        <Alert variant="info">
          Your wishlist is empty. <Link to="/products">Browse products →</Link>
        </Alert>
      ) : (
        <Row className="g-3">
          {items.map((it) => (
            <Col md={6} key={it.id}>
              <div className="d-flex align-items-center gap-3 border rounded p-2">
                <img src={productImage({ id: it.sku, slug: it.sku }, 120, 120)} alt="" className="thumb" onError={onImgError(it.sku)} />
                <div className="flex-grow-1">
                  <div className="fw-semibold">{it.product_name}</div>
                  <div className="price-tag">{it.unit_price} {currency}</div>
                </div>
                <div className="d-flex flex-column gap-1">
                  <Button size="sm" variant="primary" disabled={busyId === it.id} onClick={() => moveToCart(it.id)}>
                    <FeatherIcon icon="shopping-cart" size={14} /> Add
                  </Button>
                  <Button size="sm" variant="outline-danger" disabled={busyId === it.id} onClick={() => remove(it.id)}>
                    <FeatherIcon icon="trash-2" size={14} />
                  </Button>
                </div>
              </div>
            </Col>
          ))}
        </Row>
      )}
    </>
  );
}
