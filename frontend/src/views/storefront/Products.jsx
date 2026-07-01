import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Alert, Button, Col, Form, InputGroup, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, errorMessage } from 'api/client';
import ProductCard from 'components/ProductCard';

const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

export default function Products() {
  const [params, setParams] = useSearchParams();
  const category = params.get('category') || '';
  const search = params.get('search') || '';

  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [term, setTerm] = useState(search);

  useEffect(() => {
    apiGet('/storefront/categories/')
      .then((d) => setCategories(asList(d)))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setTerm(search);
    setLoading(true);
    setError('');
    const qs = new URLSearchParams({ page_size: '60' });
    if (category) qs.set('category', category);
    if (search) qs.set('search', search);
    apiGet(`/storefront/products/?${qs.toString()}`)
      .then((d) => setProducts(asList(d)))
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [category, search]);

  const patch = (mutate) => {
    const p = new URLSearchParams(params);
    mutate(p);
    setParams(p);
  };
  const pickCategory = (id) =>
    patch((p) => (id ? p.set('category', id) : p.delete('category')));
  const submitSearch = (e) => {
    e.preventDefault();
    patch((p) => (term.trim() ? p.set('search', term.trim()) : p.delete('search')));
  };

  const activeCat = categories.find((c) => c.id === category);

  return (
    <>
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <h3 className="fw-bold mb-0">{activeCat ? activeCat.name : search ? `Results for “${search}”` : 'All products'}</h3>
        <Form onSubmit={submitSearch} style={{ maxWidth: 320, width: '100%' }}>
          <InputGroup>
            <InputGroup.Text className="bg-white">
              <FeatherIcon icon="search" size={16} />
            </InputGroup.Text>
            <Form.Control placeholder="Search products…" value={term} onChange={(e) => setTerm(e.target.value)} />
          </InputGroup>
        </Form>
      </div>

      {/* Category filter chips */}
      <div className="d-flex flex-wrap gap-2 mb-4">
        <Button size="sm" variant={category ? 'outline-secondary' : 'primary'} onClick={() => pickCategory('')} className="rounded-pill">
          All
        </Button>
        {categories.map((c) => (
          <Button
            key={c.id}
            size="sm"
            variant={category === c.id ? 'primary' : 'outline-secondary'}
            onClick={() => pickCategory(c.id)}
            className="rounded-pill"
          >
            {c.name} <span className="opacity-75">({c.product_count})</span>
          </Button>
        ))}
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : products.length === 0 ? (
        <Alert variant="info">No products found.</Alert>
      ) : (
        <>
          <p className="text-muted small">{products.length} product(s)</p>
          <Row className="g-4">
            {products.map((p) => (
              <Col key={p.id} xs={6} md={4} lg={3}>
                <ProductCard product={p} />
              </Col>
            ))}
          </Row>
        </>
      )}
    </>
  );
}
