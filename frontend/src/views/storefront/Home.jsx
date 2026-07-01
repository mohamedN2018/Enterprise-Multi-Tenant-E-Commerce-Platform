import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Card, Col, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import ProductCard from 'components/ProductCard';
import { heroImage, onImgError, productImage, storeBanner, storeLogo } from 'utils/media';

const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

export default function Home() {
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiGet('/storefront/categories/'),
      apiGet('/storefront/products/?page_size=8'),
      apiGet('/storefront/stores/')
    ])
      .then(([cats, prods, sts]) => {
        setCategories(asList(cats));
        setProducts(asList(prods));
        setStores(asList(sts));
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      {/* Hero */}
      <div className="sf-hero mb-5" style={{ backgroundImage: `url(${heroImage()})` }}>
        <div className="p-4 p-md-5">
          <h1 className="fw-bold display-6 mb-2">Everything you need, from independent stores.</h1>
          <p className="lead mb-4 opacity-75" style={{ maxWidth: 560 }}>
            Thousands of products across curated shops — browse by category, add to cart and checkout in seconds.
          </p>
          <div className="d-flex gap-2">
            <Button as={Link} to="/products" variant="light" size="lg" className="fw-semibold">
              Shop all products <FeatherIcon icon="arrow-right" size={18} />
            </Button>
            <Button href="#categories" variant="outline-light" size="lg">
              Browse categories
            </Button>
          </div>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : (
        <>
          {/* Categories */}
          <div id="categories" className="d-flex align-items-center justify-content-between mb-3">
            <h4 className="sf-section-title mb-0">Shop by category</h4>
            <Link to="/products" className="text-decoration-none small">
              View all products →
            </Link>
          </div>
          <Row className="g-3 mb-5">
            {categories.map((c) => (
              <Col key={c.name} xs={6} md={4} lg={2}>
                <Link to={`/products?category=${encodeURIComponent(c.name)}`} className="text-decoration-none">
                  <div className="media-box ratio-1x1 category-tile product-card" style={{ borderRadius: 8 }}>
                    <img src={productImage({ slug: c.name }, 320, 320)} alt={c.name} onError={onImgError(c.name)} loading="lazy" />
                    <div className="cat-label">
                      <div className="fw-semibold px-1">{c.name}</div>
                      <div className="small opacity-75">{c.product_count} items</div>
                    </div>
                  </div>
                </Link>
              </Col>
            ))}
          </Row>

          {/* Featured products */}
          <div className="d-flex align-items-center justify-content-between mb-3">
            <h4 className="sf-section-title mb-0">Featured products</h4>
            <Link to="/products" className="text-decoration-none small">
              See more →
            </Link>
          </div>
          <Row className="g-4 mb-5">
            {products.map((p) => (
              <Col key={p.id} xs={6} md={4} lg={3}>
                <ProductCard product={p} />
              </Col>
            ))}
          </Row>

          {/* Stores */}
          <h4 className="sf-section-title mb-3">Our stores</h4>
          <Row className="g-4">
            {stores.map((s) => (
              <Col key={s.id} sm={6} lg={4}>
                <Card as={Link} to={`/store/${s.slug}`} className="h-100 text-decoration-none text-reset border-0 shadow-sm store-card">
                  <div className="media-box ratio-16x6">
                    <img src={storeBanner(s)} alt={s.name} onError={onImgError(s.slug)} loading="lazy" />
                  </div>
                  <Card.Body className="pt-4 position-relative">
                    <img
                      src={storeLogo(s)}
                      alt=""
                      onError={onImgError(`${s.slug}-l`)}
                      className="store-logo position-absolute"
                      style={{ width: 56, height: 56, top: -28, left: 20 }}
                    />
                    <Card.Title className="h6 mb-1">{s.name}</Card.Title>
                    <Card.Text className="text-muted small line-clamp-2" style={{ minHeight: 40 }}>
                      {s.description || 'Explore this store and its products.'}
                    </Card.Text>
                    <div className="d-flex align-items-center justify-content-between">
                      <span className="badge bg-light text-dark border">{s.currency}</span>
                      <span className="text-primary small fw-semibold">
                        Visit <FeatherIcon icon="arrow-right" size={14} />
                      </span>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        </>
      )}
    </>
  );
}
