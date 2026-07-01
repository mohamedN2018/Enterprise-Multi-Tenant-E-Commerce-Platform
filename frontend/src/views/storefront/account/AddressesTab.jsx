import { useCallback, useEffect, useState } from 'react';
import { Alert, Badge, Button, Col, Form, Modal, Row, Spinner } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { errorMessage } from 'api/client';

const BLANK = { label: '', full_name: '', line1: '', line2: '', city: '', region: '', postal_code: '', country: '', phone: '', is_default: false };
const FIELDS = [
  ['full_name', 'Full name', 12],
  ['line1', 'Address line 1', 12],
  ['line2', 'Address line 2', 12],
  ['city', 'City', 6],
  ['region', 'Region / State', 6],
  ['postal_code', 'Postal code', 6],
  ['country', 'Country (ISO-2)', 6],
  ['phone', 'Phone', 6],
  ['label', 'Label (e.g. Home)', 6]
];

export default function AddressesTab({ store }) {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [show, setShow] = useState(false);
  const [form, setForm] = useState(BLANK);
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const headers = { 'X-Store-Id': store.id };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/addresses/', { headers });
      setAddresses(Array.isArray(res.data) ? res.data : res.data?.results || []);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.id]);

  useEffect(() => {
    load();
  }, [load]);

  const openNew = () => { setEditing(null); setForm(BLANK); setShow(true); };
  const openEdit = (a) => { setEditing(a); setForm({ ...BLANK, ...a }); setShow(true); };

  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (editing) await api.patch(`/addresses/${editing.id}/`, form, { headers });
      else await api.post('/addresses/', form, { headers });
      setShow(false);
      load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm('Delete this address?')) return;
    await api.delete(`/addresses/${id}/`, { headers }).then(load).catch((e) => setError(errorMessage(e)));
  };
  const setDefault = async (id) => {
    await api.post(`/addresses/${id}/default/`, {}, { headers }).then(load).catch((e) => setError(errorMessage(e)));
  };

  if (loading) return <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div>;

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <span className="text-muted small">{addresses.length} address(es)</span>
        <Button size="sm" variant="primary" onClick={openNew}>
          <FeatherIcon icon="plus" size={14} /> Add address
        </Button>
      </div>
      {error && <Alert variant="danger">{error}</Alert>}
      {addresses.length === 0 ? (
        <Alert variant="info">No saved addresses yet.</Alert>
      ) : (
        <Row className="g-3">
          {addresses.map((a) => (
            <Col md={6} key={a.id}>
              <div className="border rounded p-3 h-100">
                <div className="d-flex justify-content-between">
                  <strong>{a.full_name || a.label || 'Address'}</strong>
                  {a.is_default && <Badge bg="primary">Default</Badge>}
                </div>
                <div className="small text-muted">
                  {a.line1}
                  {a.line2 ? `, ${a.line2}` : ''}
                  <br />
                  {[a.city, a.region, a.postal_code].filter(Boolean).join(', ')}
                  <br />
                  {a.country} {a.phone && `· ${a.phone}`}
                </div>
                <div className="mt-2 d-flex gap-2">
                  {!a.is_default && (
                    <Button size="sm" variant="link" className="p-0" onClick={() => setDefault(a.id)}>
                      Set default
                    </Button>
                  )}
                  <Button size="sm" variant="link" className="p-0" onClick={() => openEdit(a)}>Edit</Button>
                  <Button size="sm" variant="link" className="p-0 text-danger" onClick={() => remove(a.id)}>Delete</Button>
                </div>
              </div>
            </Col>
          ))}
        </Row>
      )}

      <Modal show={show} onHide={() => setShow(false)} centered>
        <Form onSubmit={save}>
          <Modal.Header closeButton>
            <Modal.Title className="h6">{editing ? 'Edit address' : 'New address'}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {error && <Alert variant="danger" className="py-2">{error}</Alert>}
            <Row className="g-2">
              {FIELDS.map(([name, label, size]) => (
                <Col xs={size} key={name}>
                  <Form.Label className="small mb-1">{label}</Form.Label>
                  <Form.Control size="sm" value={form[name] || ''} onChange={(e) => setForm((f) => ({ ...f, [name]: e.target.value }))} required={['line1', 'city', 'country'].includes(name)} />
                </Col>
              ))}
              <Col xs={12} className="mt-2">
                <Form.Check type="switch" label="Set as default" checked={Boolean(form.is_default)} onChange={(e) => setForm((f) => ({ ...f, is_default: e.target.checked }))} />
              </Col>
            </Row>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="link" onClick={() => setShow(false)}>Cancel</Button>
            <Button type="submit" variant="primary" disabled={busy}>{busy ? <Spinner animation="border" size="sm" /> : 'Save'}</Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}
