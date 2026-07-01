import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Card, Carousel, Col, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import ProductCard from 'components/ProductCard';
import { heroImage, onImgError, productImage, storeBanner, storeLogo } from 'utils/media';

const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

const SLIDES = [
  {
    bg: heroImage(1600, 520),
    title: 'Everything you need, from independent stores.',
    text: 'Thousands of products across curated shops — browse, add to cart and checkout in seconds.',
    cta: 'Shop all products',
    to: '/products'
  },
  {
    bg: 'https://picsum.photos/seed/marketplace-deals/1600/520',
    title: 'Mega deals — up to 30% off.',
    text: 'Limited-time offers across electronics, home, fashion and more.',
    cta: "See today's deals",
    to: '/products?on_sale=1'
  },
  {
    bg: 'https://picsum.photos/seed/marketplace-new/1600/520',
    title: 'Ten shops. One cart. Free shipping over $100.',
    text: 'Discover independent sellers and their latest arrivals.',
    cta: 'Browse stores',
    to: '/products'
  }
];

export default function Home() {
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [deals, setDeals] = useState([]);
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiGet('/storefront/categories/'),
      apiGet('/storefront/products/?page_size=8'),
      apiGet('/storefront/products/?on_sale=1&page_size=8'),
      apiGet('/storefront/stores/')
    ])
      .then(([cats, prods, dls, sts]) => {
        setCategories(asList(cats));
        setProducts(asList(prods));
        setDeals(asList(dls));
        setStores(asList(sts));
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      {/* Hero carousel */}
      <Carousel className="mb-5 sf-hero-carousel" fade interval={5000}>
        {SLIDES.map((s, i) => (
          <Carousel.Item key={i}>
            <div className="sf-slide" style={{ backgroundImage: `url(${s.bg})` }}>
              <div className="p-4 p-md-5" style={{ maxWidth: 640 }}>
                <h1 className="fw-bold display-6 mb-2">{s.title}</h1>
                <p className="lead mb-4 opacity-75">{s.text}</p>
                <Button as={Link} to={s.to} variant="light" size="lg" className="fw-semibold">
                  {s.cta} <FeatherIcon icon="arrow-right" size={18} />
                </Button>
              </div>
            </div>
          </Carousel.Item>
        ))}
      </Carousel>

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

          {/* Today's deals */}
          {deals.length > 0 && (
            <>
              <div className="d-flex align-items-center justify-content-between mb-3">
                <h4 className="sf-section-title mb-0 text-danger">
                  <FeatherIcon icon="zap" size={18} className="me-1" />
                  Today&apos;s deals
                </h4>
                <Link to="/products?on_sale=1" className="text-decoration-none small">
                  All deals →
                </Link>
              </div>
              <Row className="g-4 mb-5">
                {deals.slice(0, 4).map((p) => (
                  <Col key={p.id} xs={6} md={4} lg={3}>
                    <ProductCard product={p} />
                  </Col>
                ))}
              </Row>
            </>
          )}

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
