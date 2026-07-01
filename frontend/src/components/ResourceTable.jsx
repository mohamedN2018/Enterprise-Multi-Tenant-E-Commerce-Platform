import { useCallback, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { Link, useNavigate } from 'react-router-dom';
import { Badge, Button, Card, Spinner, Table } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { apiDelete, errorMessage } from 'api/client';
import { useStore } from 'contexts/StoreContext';
import ResourceForm from 'components/ResourceForm';

const PAGE_SIZE = 20;

const titleize = (key) => key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const BADGE_MAP = {
  active: 'success',
  approved: 'success',
  confirmed: 'success',
  paid: 'success',
  captured: 'success',
  received: 'success',
  completed: 'success',
  published: 'success',
  cleared: 'success',
  rewarded: 'success',
  pending: 'warning',
  partial: 'warning',
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

export default function ResourceTable({ resource }) {
  const { endpoint, columns, fields, detail, key: resourceKey } = resource;
  const { activeId } = useStore();
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formShow, setFormShow] = useState(false);
  const [editRecord, setEditRecord] = useState(null);

  const canWrite = Boolean(fields?.length);
  const hasRowActions = canWrite || detail;

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

  const openCreate = () => {
    setEditRecord(null);
    setFormShow(true);
  };
  const openEdit = (row) => {
    setEditRecord(row);
    setFormShow(true);
  };
  const remove = async (row) => {
    if (!window.confirm('Delete this record? This cannot be undone.')) return;
    try {
      await apiDelete(`${endpoint}${row.id}/`);
      load();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const totalPages = meta?.total_pages || 1;
  const colCount = resolvedColumns.length + (hasRowActions ? 1 : 0);

  return (
    <Card>
      <Card.Header className="d-flex align-items-center justify-content-between">
        <h5 className="mb-0">{resource.label}</h5>
        <div className="d-flex gap-2">
          <Button size="sm" variant="outline-secondary" onClick={load} title="Refresh">
            <FeatherIcon icon="refresh-cw" size={16} />
          </Button>
          {canWrite && (
            <Button size="sm" variant="primary" onClick={openCreate}>
              <FeatherIcon icon="plus" size={16} className="me-1" />
              New
            </Button>
          )}
        </div>
      </Card.Header>
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
                  {hasRowActions && <th className="text-end">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={colCount} className="text-center text-muted py-4">
                      No records.
                    </td>
                  </tr>
                )}
                {rows.map((row, i) => (
                  <tr key={row.id || i}>
                    {resolvedColumns.map((c) => {
                      const raw = row[c.key];
                      const value = c.format ? c.format(raw, row) : raw;
                      const cell =
                        c.badge && value != null && value !== '—' ? (
                          <CellBadge value={value} />
                        ) : value == null || value === '' ? (
                          '—'
                        ) : (
                          String(value)
                        );
                      return (
                        <td key={c.key}>
                          {detail && c === resolvedColumns[0] ? (
                            <Link to={`/admin/r/${resourceKey}/${row.id}`} state={{ record: row }}>
                              {cell}
                            </Link>
                          ) : (
                            cell
                          )}
                        </td>
                      );
                    })}
                    {hasRowActions && (
                      <td className="text-end text-nowrap">
                        {detail && (
                          <Button
                            size="sm"
                            variant="link"
                            className="p-0 me-3"
                            onClick={() => navigate(`/admin/r/${resourceKey}/${row.id}`, { state: { record: row } })}
                            title="View"
                          >
                            <FeatherIcon icon="eye" size={16} />
                          </Button>
                        )}
                        {canWrite && (
                          <>
                            <Button size="sm" variant="link" className="p-0 me-3" onClick={() => openEdit(row)} title="Edit">
                              <FeatherIcon icon="edit-2" size={16} />
                            </Button>
                            <Button size="sm" variant="link" className="p-0 text-danger" onClick={() => remove(row)} title="Delete">
                              <FeatherIcon icon="trash-2" size={16} />
                            </Button>
                          </>
                        )}
                      </td>
                    )}
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
                  <Button size="sm" variant="outline-secondary" disabled={!meta.next} onClick={() => setPage((p) => p + 1)}>
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card.Body>

      {canWrite && (
        <ResourceForm show={formShow} onHide={() => setFormShow(false)} resource={resource} record={editRecord} onSaved={load} />
      )}
    </Card>
  );
}

ResourceTable.propTypes = {
  resource: PropTypes.object.isRequired
};
