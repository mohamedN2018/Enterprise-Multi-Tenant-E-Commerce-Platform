import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Card, Spinner, Table } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';

export default function Cart() {
  const { isAuthenticated } = useAuth();
  const { cart, shopStore, loading, updateItem, removeItem } = useCart();
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState('');

  const currency = shopStore?.currency || '';

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
                      <div className="fw-semibold">{it.product_name}</div>
                      <div className="small text-muted">{it.sku}</div>
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

            <div className="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
              <Button as={Link} to="/" variant="link" className="text-decoration-none">
                <FeatherIcon icon="arrow-left" size={16} /> Continue shopping
              </Button>
              <div className="text-end">
                <div className="text-muted small">
                  Subtotal: {cart.subtotal} {currency}
                  {Number(cart.discount) > 0 && ` · Discount: −${cart.discount} ${currency}`}
                </div>
                <div className="h5 mb-2">
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
