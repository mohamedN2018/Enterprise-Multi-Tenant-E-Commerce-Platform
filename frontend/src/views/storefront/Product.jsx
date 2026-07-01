import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Alert, Button, Card, Col, Form, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';

export default function Product() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { setShopStore, addItem } = useCart();
  const [product, setProduct] = useState(null);
  const [variantId, setVariantId] = useState('');
  const [qty, setQty] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError('');
    apiGet(`/storefront/products/${id}/`)
      .then((p) => {
        setProduct(p);
        setShopStore({ id: p.store, slug: p.store_slug, name: p.store_slug, currency: p.currency });
        const def = (p.variants || []).find((v) => v.is_default) || (p.variants || [])[0];
        if (def) setVariantId(def.id);
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [id, setShopStore]);

  const variants = product?.variants || [];
  const selected = variants.find((v) => v.id === variantId);

  const onAdd = async () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: `/product/${id}` } });
      return;
    }
    setBusy(true);
    setError('');
    setMsg('');
    try {
      await addItem(variantId, Number(qty) || 1);
      setMsg('Added to cart.');
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
      </div>
    );
  }
  if (error && !product) return <Alert variant="danger">{error}</Alert>;
  if (!product) return <Alert variant="warning">Product not found.</Alert>;

  const outOfStock = selected && selected.in_stock === false;

  return (
    <>
      {product.store_slug && (
        <Link to={`/store/${product.store_slug}`} className="text-decoration-none small text-muted">
          <FeatherIcon icon="arrow-left" size={14} /> Back to store
        </Link>
      )}
      <Row className="g-4 mt-1">
        <Col md={5}>
          <Card className="border-0 shadow-sm">
            <div className="d-flex align-items-center justify-content-center bg-light text-secondary" style={{ height: 300 }}>
              <FeatherIcon icon="package" size={80} />
            </div>
          </Card>
        </Col>
        <Col md={7}>
          <h3 className="fw-bold mb-2">{product.name}</h3>
          <div className="h4 text-primary mb-3">
            {selected ? `${selected.price} ${product.currency}` : product.price ? `${product.price} ${product.currency}` : '—'}
          </div>
          {product.description && <p className="text-muted">{product.description}</p>}

          {msg && <Alert variant="success">{msg} <Link to="/cart">View cart →</Link></Alert>}
          {error && <Alert variant="danger">{error}</Alert>}

          {variants.length > 1 && (
            <Form.Group className="mb-3" style={{ maxWidth: 320 }}>
              <Form.Label>Option</Form.Label>
              <Form.Select value={variantId} onChange={(e) => setVariantId(e.target.value)}>
                {variants.map((v) => (
                  <option key={v.id} value={v.id} disabled={v.in_stock === false}>
                    {v.name || v.sku} — {v.price} {product.currency}
                    {v.in_stock === false ? ' (out of stock)' : ''}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          )}

          <div className="d-flex align-items-end gap-2 mb-3">
            <Form.Group style={{ width: 90 }}>
              <Form.Label>Qty</Form.Label>
              <Form.Control type="number" min={1} value={qty} onChange={(e) => setQty(e.target.value)} />
            </Form.Group>
            <Button variant="primary" onClick={onAdd} disabled={busy || !variantId || outOfStock}>
              {busy ? <Spinner animation="border" size="sm" /> : (
                <>
                  <FeatherIcon icon="shopping-cart" size={16} className="me-1" />
                  {outOfStock ? 'Out of stock' : 'Add to cart'}
                </>
              )}
            </Button>
          </div>
          {!isAuthenticated && <div className="small text-muted">You&apos;ll be asked to sign in to add items.</div>}
        </Col>
      </Row>
    </>
  );
}
