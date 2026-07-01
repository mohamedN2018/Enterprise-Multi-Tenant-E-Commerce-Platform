import { useCallback, useEffect, useState } from 'react';
import { Alert, Badge, Button, Card, Col, Form, InputGroup, Row, Spinner, Table } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import api, { errorMessage } from 'api/client';
import { useStore } from 'contexts/StoreContext';

const ROLES = ['employee', 'manager', 'owner'];
const ROLE_VARIANT = { owner: 'primary', manager: 'info', employee: 'secondary' };

export default function Team() {
  const { activeStore } = useStore();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('employee');
  const [busy, setBusy] = useState(false);

  const base = activeStore ? `/stores/${activeStore.id}/members/` : null;

  const load = useCallback(async () => {
    if (!base) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.get(base);
      setMembers(Array.isArray(res.data) ? res.data : res.data?.results || []);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [base]);

  useEffect(() => {
    load();
  }, [load]);

  const invite = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await api.post(base, { email: email.trim(), role });
      setNotice(`${email.trim()} added as ${role}.`);
      setEmail('');
      setRole('employee');
      load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const changeRole = async (m, newRole) => {
    setError('');
    try {
      await api.patch(`${base}${m.id}/`, { role: newRole });
      load();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const remove = async (m) => {
    if (!window.confirm(`Remove ${m.user_email} from this store's team?`)) return;
    setError('');
    try {
      await api.delete(`${base}${m.id}/`);
      load();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  if (!activeStore) return <Alert variant="info">Select a store from the top bar to manage its team.</Alert>;

  return (
    <Row className="g-4">
      <Col md={12}>
        <div className="d-flex align-items-center justify-content-between mb-1">
          <h5 className="mb-0">Team — {activeStore.name}</h5>
          <span className="text-muted small">{members.length} member(s)</span>
        </div>
        <p className="text-muted small">
          Store owners and managers can invite staff. Roles: <strong>owner</strong> (full control),{' '}
          <strong>manager</strong> (manage catalog, orders, staff invites), <strong>employee</strong> (day-to-day operations).
        </p>
      </Col>

      <Col lg={4}>
        <Card>
          <Card.Header>
            <h6 className="mb-0">Invite a team member</h6>
          </Card.Header>
          <Card.Body>
            {notice && <Alert variant="success" className="py-2">{notice}</Alert>}
            {error && <Alert variant="danger" className="py-2">{error}</Alert>}
            <Form onSubmit={invite}>
              <Form.Group className="mb-3">
                <Form.Label>Email</Form.Label>
                <InputGroup>
                  <InputGroup.Text>
                    <FeatherIcon icon="mail" size={16} />
                  </InputGroup.Text>
                  <Form.Control type="email" placeholder="staff@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
                </InputGroup>
                <Form.Text className="text-muted">The person must already have an account.</Form.Text>
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Role</Form.Label>
                <Form.Select value={role} onChange={(e) => setRole(e.target.value)}>
                  {ROLES.filter((r) => r !== 'owner').map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
              <Button type="submit" variant="primary" disabled={busy}>
                {busy ? <Spinner animation="border" size="sm" /> : (
                  <>
                    <FeatherIcon icon="user-plus" size={16} className="me-1" /> Add member
                  </>
                )}
              </Button>
            </Form>
          </Card.Body>
        </Card>
      </Col>

      <Col lg={8}>
        <Card>
          <Card.Header>
            <h6 className="mb-0">Members</h6>
          </Card.Header>
          <Card.Body className="p-0">
            {loading ? (
              <div className="text-center py-5">
                <Spinner animation="border" variant="primary" />
              </div>
            ) : (
              <Table responsive hover className="align-middle mb-0">
                <thead>
                  <tr>
                    <th className="ps-3">Member</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th className="text-end pe-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {members.length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-center text-muted py-4">No team members yet.</td>
                    </tr>
                  )}
                  {members.map((m) => (
                    <tr key={m.id}>
                      <td className="ps-3">{m.user_email}</td>
                      <td>
                        {m.role === 'owner' ? (
                          <Badge bg={ROLE_VARIANT.owner}>owner</Badge>
                        ) : (
                          <Form.Select size="sm" value={m.role} style={{ maxWidth: 150 }} onChange={(e) => changeRole(m, e.target.value)}>
                            {ROLES.map((r) => (
                              <option key={r} value={r}>
                                {r}
                              </option>
                            ))}
                          </Form.Select>
                        )}
                      </td>
                      <td>
                        <Badge bg={m.is_active ? 'success' : 'secondary'}>{m.is_active ? 'active' : 'inactive'}</Badge>
                      </td>
                      <td className="text-end pe-3">
                        {m.role !== 'owner' && (
                          <Button size="sm" variant="link" className="text-danger p-0" onClick={() => remove(m)} title="Remove">
                            <FeatherIcon icon="trash-2" size={16} />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
}
