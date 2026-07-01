import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Card, Col, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';

export default function Checkout() {
  const { isAuthenticated } = useAuth();
  const { cart, shopStore, checkout } = useCart();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [order, setOrder] = useState(null);

  const currency = shopStore?.currency || '';

  if (!isAuthenticated) {
    return (
      <Alert variant="info">
        Please <Link to="/login">sign in</Link> to check out.
      </Alert>
    );
  }

  // Order placed — confirmation view.
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
          <Button as={Link} to="/" variant="outline-secondary">
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
        Your cart is empty. <Link to="/">Browse stores →</Link>
      </Alert>
    );
  }

  const placeOrder = async () => {
    setBusy(true);
    setError('');
    try {
      setOrder(await checkout());
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h3 className="fw-bold mb-3">Checkout</h3>
      {error && <Alert variant="danger">{error}</Alert>}
      <Row className="g-4">
        <Col md={7}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-white">
              <strong>Order summary</strong> — {shopStore?.name}
            </Card.Header>
            <Card.Body>
              {items.map((it) => (
                <div key={it.id} className="d-flex justify-content-between border-bottom py-2">
                  <span>
                    {it.product_name} <span className="text-muted small">× {it.quantity}</span>
                  </span>
                  <span>
                    {it.line_total} {currency}
                  </span>
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
                <span>
                  {cart.subtotal} {currency}
                </span>
              </div>
              {Number(cart.discount) > 0 && (
                <div className="d-flex justify-content-between text-success">
                  <span>Discount</span>
                  <span>
                    −{cart.discount} {currency}
                  </span>
                </div>
              )}
              <div className="d-flex justify-content-between h5 mt-2 pt-2 border-top">
                <span>Total</span>
                <span>
                  {cart.total} {currency}
                </span>
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
