import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

// react-bootstrap
import { Alert, Button, Card, Col, Form, InputGroup, Row, Spinner } from 'react-bootstrap';

// third party
import FeatherIcon from 'feather-icons-react';

// assets
import logoDark from 'assets/images/logo-dark.svg';

import { apiPost, errorMessage } from 'api/client';

// -----------------------|| SIGN UP ||-----------------------//

export default function SignUp1() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '', password_confirm: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await apiPost('/auth/register/', form);
      navigate('/login', { state: { registered: true } });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-content text-center">
        <Card className="borderless">
          <Row className="align-items-center text-center">
            <Col>
              <Card.Body className="card-body">
                <img src={logoDark} alt="" className="img-fluid mb-4" />
                <h4 className="mb-3 f-w-400">Create your account</h4>
                {error && <Alert variant="danger">{error}</Alert>}
                <Form onSubmit={onSubmit}>
                  <InputGroup className="mb-3">
                    <InputGroup.Text>
                      <FeatherIcon icon="mail" />
                    </InputGroup.Text>
                    <Form.Control type="email" placeholder="Email address" value={form.email} onChange={set('email')} required />
                  </InputGroup>
                  <InputGroup className="mb-3">
                    <InputGroup.Text>
                      <FeatherIcon icon="lock" />
                    </InputGroup.Text>
                    <Form.Control type="password" placeholder="Password" value={form.password} onChange={set('password')} required />
                  </InputGroup>
                  <InputGroup className="mb-4">
                    <InputGroup.Text>
                      <FeatherIcon icon="check" />
                    </InputGroup.Text>
                    <Form.Control
                      type="password"
                      placeholder="Confirm password"
                      value={form.password_confirm}
                      onChange={set('password_confirm')}
                      required
                    />
                  </InputGroup>
                  <Button type="submit" className="btn btn-block btn-primary mb-4 w-100" disabled={busy}>
                    {busy ? <Spinner animation="border" size="sm" /> : 'Sign up'}
                  </Button>
                </Form>
                <p className="mb-2">
                  Already have an account?{' '}
                  <NavLink to="/login" className="f-w-400">
                    Sign in
                  </NavLink>
                </p>
              </Card.Body>
            </Col>
          </Row>
        </Card>
      </div>
    </div>
  );
}
