import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Alert, Col, Form, InputGroup, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import ProductCard from 'components/ProductCard';
import { useCart } from 'contexts/CartContext';
import { onImgError, storeBanner } from 'utils/media';

export default function Store() {
  const { slug } = useParams();
  const { setShopStore } = useCart();
  const [store, setStore] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [q, setQ] = useState('');

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

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return products;
    return products.filter((p) => p.name.toLowerCase().includes(term));
  }, [products, q]);

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
      <Link to="/" className="text-decoration-none small text-muted">
        <FeatherIcon icon="arrow-left" size={14} /> All stores
      </Link>

      <div className="media-box ratio-16x6 rounded-3 shadow-sm mt-2 mb-4 position-relative">
        <img src={storeBanner(store)} alt={store?.name} onError={onImgError(slug)} />
        <div className="position-absolute bottom-0 start-0 w-100 p-3 p-md-4 text-white" style={{ background: 'linear-gradient(0deg, rgba(0,0,0,.65), transparent)' }}>
          <h3 className="fw-bold mb-1">{store?.name}</h3>
          {store?.description && <p className="mb-0 small opacity-75">{store.description}</p>}
        </div>
      </div>

      <div className="d-flex flex-wrap gap-2 align-items-center justify-content-between mb-3">
        <h5 className="fw-bold mb-0">Products <span className="text-muted fw-normal">({filtered.length})</span></h5>
        <InputGroup style={{ maxWidth: 280 }}>
          <InputGroup.Text className="bg-white">
            <FeatherIcon icon="search" size={16} />
          </InputGroup.Text>
          <Form.Control placeholder="Search products…" value={q} onChange={(e) => setQ(e.target.value)} />
        </InputGroup>
      </div>

      {filtered.length === 0 ? (
        <Alert variant="info">No products found.</Alert>
      ) : (
        <Row className="g-4">
          {filtered.map((p) => (
            <Col key={p.id} xs={6} md={4} lg={3}>
              <ProductCard product={p} />
            </Col>
          ))}
        </Row>
      )}
    </>
  );
}
