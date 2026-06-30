import { useCallback, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { Badge, Button, Card, Spinner, Table } from 'react-bootstrap';

import api, { errorMessage } from 'api/client';
import { useStore } from 'contexts/StoreContext';

const PAGE_SIZE = 20;

const titleize = (key) =>
  key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const BADGE_MAP = {
  active: 'success',
  approved: 'success',
  confirmed: 'success',
  paid: 'success',
  received: 'success',
  completed: 'success',
  published: 'success',
  cleared: 'success',
  rewarded: 'success',
  pending: 'warning',
  draft: 'secondary',
  submitted: 'info',
  review: 'warning',
  processing: 'info',
  requested: 'info',
  rejected: 'danger',
  cancelled: 'danger',
  failed: 'danger',
  reject: 'danger',
  yes: 'success',
  no: 'secondary',
  true: 'success',
  false: 'secondary'
};

function CellBadge({ value }) {
  const variant = BADGE_MAP[String(value).toLowerCase()] || 'light-secondary';
  return <Badge bg={variant.replace('light-', '')}>{String(value)}</Badge>;
}
CellBadge.propTypes = { value: PropTypes.any };

const isScalar = (v) => v == null || ['string', 'number', 'boolean'].includes(typeof v);

export default function ResourceTable({ endpoint, columns }) {
  const { activeId } = useStore();
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(endpoint, { params: { page, page_size: PAGE_SIZE } });
      setRows(Array.isArray(res.data) ? res.data : res.data?.results || []);
      setMeta(res.$meta?.pagination || null);
    } catch (err) {
      setError(errorMessage(err));
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [endpoint, page]);

  useEffect(() => {
    setPage(1);
  }, [endpoint, activeId]);

  useEffect(() => {
    load();
  }, [load, activeId]);

  const resolvedColumns = useMemo(() => {
    if (columns?.length) return columns;
    const sample = rows[0] || {};
    return Object.keys(sample)
      .filter((k) => k !== 'id' && isScalar(sample[k]))
      .slice(0, 7)
      .map((k) => ({ key: k, label: titleize(k) }));
  }, [columns, rows]);

  const totalPages = meta?.total_pages || 1;

  return (
    <Card>
      <Card.Body>
        {error && <div className="alert alert-danger mb-3">{error}</div>}
        {loading ? (
          <div className="text-center py-5">
            <Spinner animation="border" variant="primary" />
          </div>
        ) : (
          <>
            <Table responsive hover className="mb-0">
              <thead>
                <tr>
                  {resolvedColumns.map((c) => (
                    <th key={c.key}>{c.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={resolvedColumns.length} className="text-center text-muted py-4">
                      No records.
                    </td>
                  </tr>
                )}
                {rows.map((row, i) => (
                  <tr key={row.id || i}>
                    {resolvedColumns.map((c) => {
                      const raw = row[c.key];
                      const value = c.format ? c.format(raw, row) : raw;
                      return (
                        <td key={c.key}>
                          {c.badge && value != null && value !== '—' ? (
                            <CellBadge value={value} />
                          ) : value == null || value === '' ? (
                            '—'
                          ) : (
                            String(value)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </Table>
            {meta && (
              <div className="d-flex align-items-center justify-content-between mt-3">
                <span className="text-muted">
                  {meta.count ?? rows.length} record(s) · page {meta.page || page} / {totalPages}
                </span>
                <div>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    className="me-2"
                    disabled={!meta.previous}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    Previous
                  </Button>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    disabled={!meta.next}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card.Body>
    </Card>
  );
}

ResourceTable.propTypes = {
  endpoint: PropTypes.string.isRequired,
  columns: PropTypes.array
};
