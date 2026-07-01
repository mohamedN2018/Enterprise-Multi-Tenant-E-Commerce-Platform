import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Card, Col, Form, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';
import { onImgError, productImage } from 'utils/media';

const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

export default function Checkout() {
  const { isAuthenticated } = useAuth();
  const { cart, shopStore, checkout } = useCart();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [order, setOrder] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [methods, setMethods] = useState([]);
  const [addressId, setAddressId] = useState('');
  const [methodId, setMethodId] = useState('');

  const currency = shopStore?.currency || '';
  const headers = shopStore ? { 'X-Store-Id': shopStore.id } : {};

  const loadMethods = useCallback(
    async (country) => {
      if (!shopStore) return;
      const res = await api
        .get('/shipping/methods/', { headers: { 'X-Store-Id': shopStore.id }, params: country ? { country } : {} })
        .then((r) => asList(r.data))
        .catch(() => []);
      setMethods(res);
    },
    [shopStore]
  );

  useEffect(() => {
    if (!shopStore) return;
    api
      .get('/addresses/', { headers: { 'X-Store-Id': shopStore.id } })
      .then((r) => {
        const list = asList(r.data);
        setAddresses(list);
        const def = list.find((a) => a.is_default);
        if (def) setAddressId(def.id);
      })
      .catch(() => {});
    loadMethods();
  }, [shopStore, loadMethods]);

  if (!isAuthenticated) {
    return (
      <Alert variant="info">
        Please <Link to="/login">sign in</Link> to check out.
      </Alert>
    );
  }

  if (order) {
    return (
      <div className="text-center py-4" style={{ maxWidth: 520, margin: '0 auto' }}>
        <div className="text-success mb-3">
          <FeatherIcon icon="check-circle" size={56} />
        </div>
        <h3 className="fw-bold">Order placed!</h3>
        <p className="text-muted">
          Order <strong>{order.number}</strong> — {order.total} {order.currency || currency}
        </p>
        <div className="d-flex gap-2 justify-content-center mt-4">
          <Button as={Link} to="/account" variant="primary">
            My orders
          </Button>
          <Button as={Link} to="/products" variant="outline-secondary">
            Continue shopping
          </Button>
        </div>
      </div>
    );
  }

  const items = cart?.items || [];
  if (items.length === 0) {
    return (
      <Alert variant="info">
        Your cart is empty. <Link to="/products">Browse products →</Link>
      </Alert>
    );
  }

  const onAddress = (id) => {
    setAddressId(id);
    const addr = addresses.find((a) => a.id === id);
    loadMethods(addr?.country);
    setMethodId('');
  };

  const placeOrder = async () => {
    setBusy(true);
    setError('');
    try {
      setOrder(await checkout({ address_id: addressId || null, shipping_method_id: methodId || null }));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const selectedMethod = methods.find((m) => m.id === methodId);

  return (
    <>
      <h3 className="fw-bold mb-3">Checkout</h3>
      {error && <Alert variant="danger">{error}</Alert>}
      <Row className="g-4">
        <Col md={7}>
          <Card className="border-0 shadow-sm mb-3">
            <Card.Header className="bg-white fw-semibold">Shipping address</Card.Header>
            <Card.Body>
              {addresses.length === 0 ? (
                <div className="small text-muted">
                  No saved addresses. <Link to="/account">Add one in your account</Link> (optional).
                </div>
              ) : (
                <Form.Select value={addressId} onChange={(e) => onAddress(e.target.value)}>
                  <option value="">No address</option>
                  {addresses.map((a) => (
                    <option key={a.id} value={a.id}>
                      {[a.full_name || a.label, a.line1, a.city, a.country].filter(Boolean).join(', ')}
                    </option>
                  ))}
                </Form.Select>
              )}
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm mb-3">
            <Card.Header className="bg-white fw-semibold">Shipping method</Card.Header>
            <Card.Body>
              {methods.length === 0 ? (
                <div className="small text-muted">No shipping methods — delivery is free for this order.</div>
              ) : (
                <>
                  <Form.Check
                    type="radio"
                    name="ship"
                    id="ship-none"
                    label="No shipping (free)"
                    checked={!methodId}
                    onChange={() => setMethodId('')}
                    className="mb-2"
                  />
                  {methods.map((m) => (
                    <Form.Check
                      key={m.id}
                      type="radio"
                      name="ship"
                      id={`ship-${m.id}`}
                      checked={methodId === m.id}
                      onChange={() => setMethodId(m.id)}
                      className="mb-2"
                      label={
                        <span className="d-flex justify-content-between" style={{ width: 260 }}>
                          <span>{m.name} <span className="text-muted small">· {m.zone_name}</span></span>
                          <span>{Number(m.price) === 0 ? 'Free' : `${m.price} ${currency}`}</span>
                        </span>
                      }
                    />
                  ))}
                </>
              )}
            </Card.Body>
          </Card>

          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-white fw-semibold">Items</Card.Header>
            <Card.Body>
              {items.map((it) => (
                <div key={it.id} className="d-flex align-items-center justify-content-between border-bottom py-2">
                  <span className="d-flex align-items-center gap-2">
                    <img src={productImage({ id: it.sku, slug: it.sku }, 100, 100)} alt="" className="thumb" style={{ width: 40, height: 40 }} onError={onImgError(it.sku)} />
                    {it.product_name} <span className="text-muted small">× {it.quantity}</span>
                  </span>
                  <span>{it.line_total} {currency}</span>
                </div>
              ))}
            </Card.Body>
          </Card>
        </Col>

        <Col md={5}>
          <Card className="border-0 shadow-sm">
            <Card.Body>
              <div className="d-flex justify-content-between">
                <span className="text-muted">Subtotal</span>
                <span>{cart.subtotal} {currency}</span>
              </div>
              {Number(cart.discount) > 0 && (
                <div className="d-flex justify-content-between text-success">
                  <span>Discount{cart.coupon_code ? ` (${cart.coupon_code})` : ''}</span>
                  <span>−{cart.discount} {currency}</span>
                </div>
              )}
              {selectedMethod && (
                <div className="d-flex justify-content-between">
                  <span className="text-muted">Shipping</span>
                  <span>{Number(selectedMethod.price) === 0 ? 'Free' : `${selectedMethod.price} ${currency}`}</span>
                </div>
              )}
              <div className="small text-muted mt-1">Tax &amp; final shipping are calculated when the order is placed.</div>
              <div className="d-flex justify-content-between h5 mt-2 pt-2 border-top">
                <span>Total</span>
                <span>{cart.total} {currency}</span>
              </div>
              <Button variant="primary" className="w-100 mt-3" onClick={placeOrder} disabled={busy}>
                {busy ? <Spinner animation="border" size="sm" /> : 'Place order'}
              </Button>
              <div className="small text-muted text-center mt-2">Demo checkout — no real payment is taken.</div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
}
