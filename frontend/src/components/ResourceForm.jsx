import { useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { Alert, Button, Col, Form, Modal, Row, Spinner } from 'react-bootstrap';

import api, { apiPatch, apiPost, errorMessage } from 'api/client';

// Generic create/edit modal driven by a resource's `fields` declaration.
//
// fields: [{ name, label, type, options?, optionsEndpoint?, optionLabel?, required?, help?, placeholder?, default?, colSize? }]
//   type ∈ text | textarea | number | money | checkbox | select | date | datetime | email
// `optionsEndpoint` turns a select into an async FK picker (fetched when the modal opens).
// When `record` is provided the modal edits it (PATCH); otherwise it creates (POST).

const emptyFor = (fields) =>
  Object.fromEntries(fields.map((f) => [f.name, f.default ?? (f.type === 'checkbox' ? false : '')]));

const fromRecord = (fields, record) =>
  Object.fromEntries(
    fields.map((f) => {
      let v = record?.[f.name];
      if (v && typeof v === 'object' && 'id' in v) v = v.id; // FK serialized as nested object
      if (f.type === 'checkbox') v = Boolean(v);
      else if (v && f.type === 'datetime') v = String(v).slice(0, 16); // ISO → "YYYY-MM-DDTHH:MM"
      else if (v && f.type === 'date') v = String(v).slice(0, 10);
      return [f.name, v ?? (f.type === 'checkbox' ? false : '')];
    })
  );

// Strip empty optional values and coerce numbers so the API gets a clean payload.
const buildPayload = (fields, values) => {
  const out = {};
  for (const f of fields) {
    let v = values[f.name];
    if (f.type === 'checkbox') {
      out[f.name] = Boolean(v);
      continue;
    }
    if (v === '' || v == null) {
      if (f.required) out[f.name] = v; // let the API report the validation error
      continue; // omit blank optionals
    }
    if (f.type === 'number' || f.type === 'money') v = Number(v);
    out[f.name] = v;
  }
  return out;
};

export default function ResourceForm({ show, onHide, resource, record, onSaved }) {
  const fields = resource.fields || [];
  const editing = Boolean(record?.id);
  const [values, setValues] = useState(() => emptyFor(fields));
  const [remoteOptions, setRemoteOptions] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!show) return;
    setError('');
    setValues(editing ? fromRecord(fields, record) : emptyFor(fields));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show, record]);

  // Load options for any FK (optionsEndpoint) fields when the modal opens.
  useEffect(() => {
    if (!show) return;
    let alive = true;
    const remote = fields.filter((f) => f.optionsEndpoint);
    remote.forEach(async (f) => {
      try {
        const res = await api.get(f.optionsEndpoint, { params: { page_size: 200 } });
        const rows = Array.isArray(res.data) ? res.data : res.data?.results || [];
        if (alive) {
          setRemoteOptions((o) => ({
            ...o,
            [f.name]: rows.map((r) => ({ value: r.id, label: r[f.optionLabel || 'name'] || r.id }))
          }));
        }
      } catch {
        /* leave the picker empty on failure */
      }
    });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [show]);

  const set = (name, value) => setValues((v) => ({ ...v, [name]: value }));

  const title = useMemo(
    () => `${editing ? 'Edit' : 'New'} ${resource.singular || resource.label.replace(/s$/, '')}`,
    [editing, resource]
  );

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const payload = buildPayload(fields, values);
      const url = editing ? `${resource.endpoint}${record.id}/` : resource.endpoint;
      const saved = editing ? await apiPatch(url, payload) : await apiPost(url, payload);
      onSaved?.(saved);
      onHide();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide} size="lg" centered backdrop="static">
      <Form onSubmit={submit}>
        <Modal.Header closeButton>
          <Modal.Title>{title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          <Row>
            {fields.map((f) => (
              <Col md={f.colSize || (f.type === 'textarea' ? 12 : 6)} key={f.name} className="mb-3">
                <Form.Group controlId={`field-${f.name}`}>
                  {f.type !== 'checkbox' && (
                    <Form.Label>
                      {f.label}
                      {f.required && <span className="text-danger ms-1">*</span>}
                    </Form.Label>
                  )}
                  {f.type === 'textarea' ? (
                    <Form.Control as="textarea" rows={3} value={values[f.name] ?? ''} onChange={(e) => set(f.name, e.target.value)} />
                  ) : f.type === 'select' ? (
                    <Form.Select value={values[f.name] ?? ''} onChange={(e) => set(f.name, e.target.value)} required={f.required}>
                      <option value="">{f.placeholder || '— select —'}</option>
                      {(remoteOptions[f.name] || f.options || []).map((o) => {
                        const val = typeof o === 'object' ? o.value : o;
                        const lbl = typeof o === 'object' ? o.label : o;
                        return (
                          <option key={val} value={val}>
                            {lbl}
                          </option>
                        );
                      })}
                    </Form.Select>
                  ) : f.type === 'checkbox' ? (
                    <Form.Check
                      type="switch"
                      label={f.label}
                      checked={Boolean(values[f.name])}
                      onChange={(e) => set(f.name, e.target.checked)}
                    />
                  ) : (
                    <Form.Control
                      type={
                        f.type === 'money' || f.type === 'number'
                          ? 'number'
                          : f.type === 'date'
                            ? 'date'
                            : f.type === 'datetime'
                              ? 'datetime-local'
                              : f.type === 'email'
                                ? 'email'
                                : 'text'
                      }
                      step={f.type === 'money' ? '0.01' : undefined}
                      placeholder={f.placeholder}
                      value={values[f.name] ?? ''}
                      onChange={(e) => set(f.name, e.target.value)}
                      required={f.required}
                    />
                  )}
                  {f.help && <Form.Text className="text-muted">{f.help}</Form.Text>}
                </Form.Group>
              </Col>
            ))}
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="link" onClick={onHide} disabled={busy}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={busy}>
            {busy ? <Spinner animation="border" size="sm" /> : editing ? 'Save changes' : 'Create'}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

ResourceForm.propTypes = {
  show: PropTypes.bool,
  onHide: PropTypes.func.isRequired,
  resource: PropTypes.object.isRequired,
  record: PropTypes.object,
  onSaved: PropTypes.func
};
