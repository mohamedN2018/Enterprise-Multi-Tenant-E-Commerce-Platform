import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';

// react-bootstrap
import { Alert, Button, Card, Col, Form, InputGroup, Row, Spinner } from 'react-bootstrap';

// third party
import FeatherIcon from 'feather-icons-react';

// assets
import logoDark from 'assets/images/logo-dark.svg';

import { errorMessage } from 'api/client';
import { useAuth } from 'contexts/AuthContext';

// -----------------------|| SIGNIN ||-----------------------//

export default function SignIn1() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('owner@demo.com');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const registered = location.state?.registered;

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await login(email, password);
      navigate('/');
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
                <h4 className="mb-3 f-w-400">Marketplace Admin</h4>
                {registered && <Alert variant="success">Account created. Please sign in.</Alert>}
                {error && <Alert variant="danger">{error}</Alert>}
                <Form onSubmit={onSubmit}>
                  <InputGroup className="mb-3">
                    <InputGroup.Text>
                      <FeatherIcon icon="mail" />
                    </InputGroup.Text>
                    <Form.Control
                      type="email"
                      placeholder="Email address"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </InputGroup>
                  <InputGroup className="mb-3">
                    <InputGroup.Text>
                      <FeatherIcon icon="lock" />
                    </InputGroup.Text>
                    <Form.Control
                      type="password"
                      placeholder="Password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </InputGroup>
                  <Button type="submit" className="btn btn-block btn-primary mb-4 w-100" disabled={busy}>
                    {busy ? <Spinner animation="border" size="sm" /> : 'Sign in'}
                  </Button>
                </Form>
                <p className="mb-0 text-muted">
                  Don&apos;t have an account?{' '}
                  <NavLink to="/register" className="f-w-400">
                    Sign up
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
