import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { Alert, Badge, Button, Card, Col, Row, Spinner, Table } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { apiGet, apiPost, errorMessage } from 'api/client';
import { findResource } from 'config/resources';
import { useStore } from 'contexts/StoreContext';
import ResourceForm from 'components/ResourceForm';

const titleize = (key) => key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
const isScalar = (v) => v == null || ['string', 'number', 'boolean'].includes(typeof v);

// Pick a human label for the record header (number > code > name > sku > id).
const headerLabel = (rec) => rec?.number || rec?.code || rec?.name || rec?.sku || rec?.id || '';

function ScalarValue({ field, value }) {
  if (value == null || value === '') return <span className="text-muted">—</span>;
  if (typeof value === 'boolean') return <Badge bg={value ? 'success' : 'secondary'}>{value ? 'Yes' : 'No'}</Badge>;
  if (field === 'status' || field === 'decision' || field === 'resolution') return <Badge bg="light-primary">{String(value)}</Badge>;
  return <span>{String(value)}</span>;
}

export default function ResourceDetail() {
  const { key, id } = useParams();
  const location = useLocation();
  const resource = findResource(key);
  const { activeStore } = useStore();

  const [record, setRecord] = useState(location.state?.record || null);
  const [loading, setLoading] = useState(!location.state?.record);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busyAction, setBusyAction] = useState('');
  const [formShow, setFormShow] = useState(false);

  const itemUrl = resource?.itemEndpoint ? resource.itemEndpoint(id) : resource ? `${resource.endpoint}${id}/` : '';

  const fetchRecord = useCallback(async () => {
    if (!itemUrl) return;
    setLoading(true);
    setError('');
    try {
      setRecord(await apiGet(itemUrl));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [itemUrl]);

  useEffect(() => {
    if (!record) fetchRecord();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (!resource) return <Alert variant="warning">Unknown resource: {key}</Alert>;
  if (!activeStore) return <Alert variant="info">Select a store to view this record.</Alert>;

  const runAction = async (action) => {
    let body = {};
    if (action.prompt) {
      const answer = window.prompt(action.prompt.label);
      if (answer == null) return;
      body = { [action.prompt.field]: answer };
    } else if (action.confirm && !window.confirm(action.confirm)) {
      return;
    }
    setBusyAction(action.key);
    setError('');
    setNotice('');
    try {
      const updated = await apiPost(action.path(record), body);
      if (updated && typeof updated === 'object' && updated.id) setRecord(updated);
      else await fetchRecord();
      setNotice(`${action.label} succeeded.`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyAction('');
    }
  };

  const scalarEntries = record ? Object.entries(record).filter(([, v]) => isScalar(v)) : [];
  const nestedTables = record
    ? Object.entries(record).filter(([, v]) => Array.isArray(v) && v.length && typeof v[0] === 'object')
    : [];
  const nestedObjects = record
    ? Object.entries(record).filter(([, v]) => v && typeof v === 'object' && !Array.isArray(v))
    : [];

  const actions = (resource.actions || []).filter((a) => !a.show || (record && a.show(record)));

  return (
    <>
      <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
        <div className="d-flex align-items-center gap-2">
          <Button as={Link} to={`/r/${key}`} variant="outline-secondary" size="sm">
            <FeatherIcon icon="arrow-left" size={16} />
          </Button>
          <h5 className="mb-0">
            {resource.singular || resource.label} · {headerLabel(record)}
          </h5>
          {record?.status && <Badge bg="light-primary">{record.status}</Badge>}
        </div>
        <div className="d-flex gap-2 flex-wrap">
          {resource.fields?.length > 0 && (
            <Button variant="outline-primary" size="sm" onClick={() => setFormShow(true)}>
              <FeatherIcon icon="edit-2" size={16} className="me-1" />
              Edit
            </Button>
          )}
          {actions.map((a) => (
            <Button key={a.key} variant={a.variant || 'secondary'} size="sm" disabled={Boolean(busyAction)} onClick={() => runAction(a)}>
              {busyAction === a.key ? <Spinner animation="border" size="sm" /> : a.label}
            </Button>
          ))}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {notice && (
        <Alert variant="success" dismissible onClose={() => setNotice('')}>
          {notice}
        </Alert>
      )}

      {loading ? (
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : !record ? (
        <Alert variant="warning">Record not found.</Alert>
      ) : (
        <Row>
          <Col lg={nestedTables.length ? 6 : 12}>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Details</h5>
              </Card.Header>
              <Card.Body>
                <Table responsive borderless className="mb-0">
                  <tbody>
                    {scalarEntries.map(([k, v]) => (
                      <tr key={k}>
                        <td className="text-muted" style={{ width: '40%' }}>
                          {titleize(k)}
                        </td>
                        <td>
                          <ScalarValue field={k} value={v} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>

            {nestedObjects.map(([k, obj]) => (
              <Card key={k}>
                <Card.Header>
                  <h6 className="mb-0">{titleize(k)}</h6>
                </Card.Header>
                <Card.Body>
                  <Table responsive borderless className="mb-0">
                    <tbody>
                      {Object.entries(obj)
                        .filter(([, v]) => isScalar(v))
                        .map(([ik, iv]) => (
                          <tr key={ik}>
                            <td className="text-muted" style={{ width: '40%' }}>
                              {titleize(ik)}
                            </td>
                            <td>
                              <ScalarValue field={ik} value={iv} />
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            ))}
          </Col>

          {nestedTables.length > 0 && (
            <Col lg={6}>
              {nestedTables.map(([k, list]) => {
                const cols = Object.keys(list[0]).filter((c) => isScalar(list[0][c]) && c !== 'id');
                return (
                  <Card key={k}>
                    <Card.Header>
                      <h6 className="mb-0">
                        {titleize(k)} <span className="text-muted">({list.length})</span>
                      </h6>
                    </Card.Header>
                    <Card.Body>
                      <Table responsive hover size="sm" className="mb-0">
                        <thead>
                          <tr>
                            {cols.map((c) => (
                              <th key={c}>{titleize(c)}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {list.map((item, idx) => (
                            <tr key={item.id || idx}>
                              {cols.map((c) => (
                                <td key={c}>{item[c] == null ? '—' : String(item[c])}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </Card.Body>
                  </Card>
                );
              })}
            </Col>
          )}
        </Row>
      )}

      {resource.fields?.length > 0 && (
        <ResourceForm show={formShow} onHide={() => setFormShow(false)} resource={resource} record={record} onSaved={(saved) => setRecord(saved)} />
      )}
    </>
  );
}
