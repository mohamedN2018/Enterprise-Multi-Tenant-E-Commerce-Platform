import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Button, Card, Col, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import { heroImage, onImgError, storeBanner, storeLogo } from 'utils/media';

export default function Home() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiGet('/storefront/stores/')
      .then((d) => setStores(Array.isArray(d) ? d : d?.results || []))
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="sf-hero mb-5" style={{ backgroundImage: `url(${heroImage()})` }}>
        <div className="p-4 p-md-5">
          <h1 className="fw-bold display-6 mb-2">Everything you need, from independent stores.</h1>
          <p className="lead mb-4 opacity-75" style={{ maxWidth: 560 }}>
            Discover curated shops on one marketplace. Browse catalogs, add to cart and checkout in seconds.
          </p>
          <Button href="#stores" variant="light" size="lg" className="fw-semibold">
            Start shopping <FeatherIcon icon="arrow-right" size={18} />
          </Button>
        </div>
      </div>

      <div id="stores" className="d-flex align-items-center justify-content-between mb-3">
        <h4 className="fw-bold mb-0">Browse stores</h4>
        <span className="text-muted small">{stores.length} store(s)</span>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : stores.length === 0 ? (
        <Alert variant="info">No stores are open yet.</Alert>
      ) : (
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
      )}
    </>
  );
}
