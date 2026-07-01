import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Card, Col, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';

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
      <div className="text-center py-4 mb-3">
        <h2 className="fw-bold mb-2">Shop the marketplace</h2>
        <p className="text-muted mb-0">Browse independent stores and their catalogs.</p>
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
              <Card as={Link} to={`/store/${s.slug}`} className="h-100 text-decoration-none text-reset shadow-sm border-0 store-card">
                <div className="d-flex align-items-center justify-content-center bg-primary bg-opacity-10 text-primary" style={{ height: 120 }}>
                  <FeatherIcon icon="shopping-bag" size={44} />
                </div>
                <Card.Body>
                  <Card.Title className="h6 mb-1">{s.name}</Card.Title>
                  <Card.Text className="text-muted small mb-2" style={{ minHeight: 40 }}>
                    {s.description || 'Explore this store.'}
                  </Card.Text>
                  <span className="badge bg-light text-dark border">{s.currency}</span>
                  <span className="text-primary small float-end">
                    Visit <FeatherIcon icon="arrow-right" size={14} />
                  </span>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </>
  );
}
