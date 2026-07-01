import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Alert, Button, Card, Col, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import { useCart } from 'contexts/CartContext';

export default function Store() {
  const { slug } = useParams();
  const { setShopStore } = useCart();
  const [store, setStore] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([apiGet(`/storefront/stores/${slug}/`), apiGet(`/storefront/stores/${slug}/products/`)])
      .then(([st, prods]) => {
        setStore(st);
        setShopStore(st);
        setProducts(Array.isArray(prods) ? prods : prods?.results || []);
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [slug, setShopStore]);

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
      </div>
    );
  }
  if (error) return <Alert variant="danger">{error}</Alert>;

  return (
    <>
      <div className="mb-4">
        <Link to="/" className="text-decoration-none small text-muted">
          <FeatherIcon icon="arrow-left" size={14} /> All stores
        </Link>
        <h3 className="fw-bold mt-2 mb-1">{store?.name}</h3>
        {store?.description && <p className="text-muted mb-0">{store.description}</p>}
      </div>

      {products.length === 0 ? (
        <Alert variant="info">This store has no products yet.</Alert>
      ) : (
        <Row className="g-4">
          {products.map((p) => (
            <Col key={p.id} xs={6} md={4} lg={3}>
              <Card className="h-100 shadow-sm border-0 product-card">
                <Link to={`/product/${p.id}`} className="text-decoration-none text-reset">
                  <div className="d-flex align-items-center justify-content-center bg-light text-secondary" style={{ height: 140 }}>
                    <FeatherIcon icon="package" size={40} />
                  </div>
                  <Card.Body className="pb-2">
                    <Card.Title className="h6 mb-1 text-truncate">{p.name}</Card.Title>
                    <div className="fw-bold text-primary">
                      {p.price ? `${p.price} ${p.currency}` : '—'}
                    </div>
                  </Card.Body>
                </Link>
                <Card.Footer className="bg-white border-0 pt-0">
                  <Button as={Link} to={`/product/${p.id}`} variant="outline-primary" size="sm" className="w-100">
                    View
                  </Button>
                </Card.Footer>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </>
  );
}
