import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Card, Form, InputGroup, Spinner, Table } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';
import { onImgError, productImage } from 'utils/media';

export default function Cart() {
  const { isAuthenticated } = useAuth();
  const { cart, shopStore, loading, updateItem, removeItem, applyCoupon, removeCoupon } = useCart();
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState('');
  const [coupon, setCoupon] = useState('');
  const [couponBusy, setCouponBusy] = useState(false);

  const currency = shopStore?.currency || '';

  const onCoupon = async (e) => {
    e.preventDefault();
    if (!coupon.trim()) return;
    setCouponBusy(true);
    setError('');
    try {
      await applyCoupon(coupon.trim());
      setCoupon('');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setCouponBusy(false);
    }
  };

  const act = async (fn) => {
    setError('');
    try {
      await fn();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyId('');
    }
  };

  if (!isAuthenticated) {
    return (
      <Alert variant="info">
        Please <Link to="/login">sign in</Link> to view your cart.
      </Alert>
    );
  }

  const items = cart?.items || [];

  return (
    <>
      <h3 className="fw-bold mb-3">Your cart</h3>
      {error && <Alert variant="danger">{error}</Alert>}

      {loading && !cart ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : items.length === 0 ? (
        <Alert variant="info">
          Your cart is empty. <Link to="/">Browse stores →</Link>
        </Alert>
      ) : (
        <Card className="border-0 shadow-sm">
          <Card.Body>
            <Table responsive className="align-middle mb-0">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Price</th>
                  <th style={{ width: 150 }}>Qty</th>
                  <th className="text-end">Line total</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <tr key={it.id}>
                    <td>
                      <div className="d-flex align-items-center gap-3">
                        <img
                          src={productImage({ id: it.sku, slug: it.sku }, 120, 120)}
                          alt=""
                          className="thumb"
                          onError={onImgError(it.sku)}
                        />
                        <div>
                          <div className="fw-semibold">{it.product_name}</div>
                          <div className="small text-muted">{it.sku}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      {it.unit_price} {currency}
                    </td>
                    <td>
                      <div className="d-flex align-items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline-secondary"
                          disabled={busyId === it.id}
                          onClick={() => {
                            setBusyId(it.id);
                            act(() => updateItem(it.id, it.quantity - 1));
                          }}
                        >
                          −
                        </Button>
                        <span>{it.quantity}</span>
                        <Button
                          size="sm"
                          variant="outline-secondary"
                          disabled={busyId === it.id}
                          onClick={() => {
                            setBusyId(it.id);
                            act(() => updateItem(it.id, it.quantity + 1));
                          }}
                        >
                          +
                        </Button>
                      </div>
                    </td>
                    <td className="text-end fw-semibold">
                      {it.line_total} {currency}
                    </td>
                    <td className="text-end">
                      <Button
                        size="sm"
                        variant="link"
                        className="text-danger p-0"
                        onClick={() => {
                          setBusyId(it.id);
                          act(() => removeItem(it.id));
                        }}
                      >
                        <FeatherIcon icon="trash-2" size={16} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            <div className="row mt-3 pt-3 border-top g-3">
              <div className="col-md-6">
                {cart.coupon_code ? (
                  <div className="d-flex align-items-center gap-2">
                    <span className="badge bg-success">Coupon: {cart.coupon_code}</span>
                    <Button size="sm" variant="link" className="text-danger p-0" onClick={removeCoupon}>
                      remove
                    </Button>
                  </div>
                ) : (
                  <Form onSubmit={onCoupon} style={{ maxWidth: 320 }}>
                    <InputGroup size="sm">
                      <Form.Control placeholder="Coupon code" value={coupon} onChange={(e) => setCoupon(e.target.value)} />
                      <Button type="submit" variant="outline-primary" disabled={couponBusy}>
                        {couponBusy ? <Spinner animation="border" size="sm" /> : 'Apply'}
                      </Button>
                    </InputGroup>
                  </Form>
                )}
                <Button as={Link} to="/" variant="link" className="text-decoration-none ps-0 mt-2">
                  <FeatherIcon icon="arrow-left" size={16} /> Continue shopping
                </Button>
              </div>
              <div className="col-md-6 text-md-end">
                <div className="text-muted">
                  Subtotal: {cart.subtotal} {currency}
                </div>
                {Number(cart.discount) > 0 && (
                  <div className="text-success">
                    Discount: −{cart.discount} {currency}
                  </div>
                )}
                <div className="h5 my-2">
                  Total: {cart.total} {currency}
                </div>
                <Button as={Link} to="/checkout" variant="primary">
                  Checkout <FeatherIcon icon="arrow-right" size={16} />
                </Button>
              </div>
            </div>
          </Card.Body>
        </Card>
      )}
    </>
  );
}
