import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Alert, Button, Col, Form, InputGroup, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { apiGet, errorMessage } from 'api/client';
import ProductCard from 'components/ProductCard';

const PAGE_SIZE = 24;
const asList = (d) => (Array.isArray(d) ? d : d?.results || []);

export default function Products() {
  const [params, setParams] = useSearchParams();
  const category = params.get('category') || '';
  const search = params.get('search') || '';

  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [term, setTerm] = useState(search);

  useEffect(() => {
    apiGet('/storefront/categories/')
      .then((d) => setCategories(asList(d)))
      .catch(() => {});
  }, []);

  const fetchPage = useCallback(
    async (pageNum, append) => {
      const qp = { page: pageNum, page_size: PAGE_SIZE };
      if (category) qp.category = category;
      if (search) qp.search = search;
      const res = await api.get('/storefront/products/', { params: qp });
      const list = asList(res.data);
      const meta = res.$meta?.pagination;
      setTotal(meta?.count ?? list.length);
      setHasNext(Boolean(meta?.next));
      setProducts((prev) => (append ? [...prev, ...list] : list));
    },
    [category, search]
  );

  useEffect(() => {
    setTerm(search);
    setLoading(true);
    setError('');
    setPage(1);
    fetchPage(1, false)
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [category, search, fetchPage]);

  const patch = (mutate) => {
    const p = new URLSearchParams(params);
    mutate(p);
    setParams(p);
  };
  const pickCategory = (id) => patch((p) => (id ? p.set('category', id) : p.delete('category')));
  const submitSearch = (e) => {
    e.preventDefault();
    patch((p) => (term.trim() ? p.set('search', term.trim()) : p.delete('search')));
  };

  const loadMore = async () => {
    setLoadingMore(true);
    const next = page + 1;
    try {
      await fetchPage(next, true);
      setPage(next);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <>
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <h3 className="sf-section-title mb-0">
          {category || (search ? `Results for “${search}”` : 'All products')}
        </h3>
        <Form onSubmit={submitSearch} style={{ maxWidth: 320, width: '100%' }}>
          <InputGroup>
            <InputGroup.Text className="bg-white">
              <FeatherIcon icon="search" size={16} />
            </InputGroup.Text>
            <Form.Control placeholder="Search products…" value={term} onChange={(e) => setTerm(e.target.value)} />
          </InputGroup>
        </Form>
      </div>

      <div className="d-flex flex-wrap gap-2 mb-4">
        <Button size="sm" variant={category ? 'outline-secondary' : 'primary'} onClick={() => pickCategory('')} className="rounded-pill">
          All
        </Button>
        {categories.map((c) => (
          <Button
            key={c.name}
            size="sm"
            variant={category === c.name ? 'primary' : 'outline-secondary'}
            onClick={() => pickCategory(c.name)}
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
          <p className="text-muted small">
            Showing {products.length} of {total} product(s)
          </p>
          <Row className="g-4">
            {products.map((p) => (
              <Col key={p.id} xs={6} md={4} lg={3}>
                <ProductCard product={p} />
              </Col>
            ))}
          </Row>
          {hasNext && (
            <div className="text-center mt-4">
              <Button variant="outline-primary" onClick={loadMore} disabled={loadingMore}>
                {loadingMore ? <Spinner animation="border" size="sm" /> : 'Load more products'}
              </Button>
            </div>
          )}
        </>
      )}
    </>
  );
}
