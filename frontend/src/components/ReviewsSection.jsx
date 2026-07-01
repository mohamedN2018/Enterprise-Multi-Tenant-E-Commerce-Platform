import { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Badge, Button, Card, Col, Form, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { apiGet, errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';
import StarRating from 'components/StarRating';

const avgOf = (s) => Number(s?.average_rating ?? 0);
const countOf = (s) => Number(s?.count ?? 0);

export default function ReviewsSection({ productId, storeId }) {
  const { isAuthenticated } = useAuth();
  const [summary, setSummary] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ rating: 5, title: '', body: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      // Public endpoint — approved reviews + summary, no auth needed.
      const data = await apiGet(`/storefront/products/${productId}/reviews/`);
      setSummary(data?.summary || null);
      setReviews(data?.results || []);
    } catch {
      setSummary(null);
      setReviews([]);
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    setMsg('');
    try {
      await api.post(
        '/reviews/',
        { product_id: productId, rating: form.rating, title: form.title, body: form.body },
        { headers: storeId ? { 'X-Store-Id': storeId } : {} }
      );
      setMsg('Thanks! Your review was submitted and is awaiting moderation.');
      setForm({ rating: 5, title: '', body: '' });
      load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-5">
      <h4 className="sf-section-title mb-3">Ratings & reviews</h4>
      {loading ? (
        <Spinner animation="border" variant="primary" />
      ) : (
        <Row className="g-4">
          <Col md={4}>
            <Card className="border-0 shadow-sm text-center">
              <Card.Body>
                <div className="display-5 fw-bold">{avgOf(summary).toFixed(1)}</div>
                <StarRating value={avgOf(summary)} size={20} />
                <div className="text-muted small mt-1">{countOf(summary)} review(s)</div>
              </Card.Body>
            </Card>

            {isAuthenticated ? (
              <Card className="border-0 shadow-sm mt-3">
                <Card.Body>
                  <h6 className="mb-2">Write a review</h6>
                  {msg && <Alert variant="success" className="py-2">{msg}</Alert>}
                  {error && <Alert variant="danger" className="py-2">{error}</Alert>}
                  <Form onSubmit={submit}>
                    <div className="mb-2">
                      <StarRating value={form.rating} size={22} onChange={(r) => setForm((f) => ({ ...f, rating: r }))} />
                    </div>
                    <Form.Control className="mb-2" placeholder="Title" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
                    <Form.Control className="mb-2" as="textarea" rows={3} placeholder="Share your experience…" value={form.body} onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))} />
                    <Button type="submit" variant="primary" size="sm" disabled={busy}>
                      {busy ? <Spinner animation="border" size="sm" /> : 'Submit review'}
                    </Button>
                  </Form>
                </Card.Body>
              </Card>
            ) : (
              <Alert variant="light" className="border mt-3 small">Sign in to write a review.</Alert>
            )}
          </Col>

          <Col md={8}>
            {reviews.length === 0 ? (
              <Alert variant="light" className="border">No reviews yet — be the first to review this product.</Alert>
            ) : (
              reviews.map((r) => (
                <Card key={r.id} className="border-0 shadow-sm mb-3">
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <StarRating value={r.rating} size={15} />
                        {r.title && <span className="fw-semibold ms-2">{r.title}</span>}
                      </div>
                      {r.is_verified_purchase && (
                        <Badge bg="success" className="text-white">
                          <FeatherIcon icon="check" size={12} /> Verified purchase
                        </Badge>
                      )}
                    </div>
                    {r.body && <p className="mb-1 mt-2">{r.body}</p>}
                    <div className="small text-muted">{r.created_at ? String(r.created_at).slice(0, 10) : ''}</div>
                  </Card.Body>
                </Card>
              ))
            )}
          </Col>
        </Row>
      )}
    </div>
  );
}

ReviewsSection.propTypes = {
  productId: PropTypes.string.isRequired,
  storeId: PropTypes.string
};
