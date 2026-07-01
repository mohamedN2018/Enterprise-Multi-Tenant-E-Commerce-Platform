import { Suspense } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Badge, Button, Container, Dropdown, Nav, Navbar } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';
import Loader from 'components/Loader/Loader';

// Public storefront chrome: brand, cart, account/login. The admin console lives
// under /admin.
export default function StoreLayout() {
  const { isAuthenticated, user, logout } = useAuth();
  const { count } = useCart();
  const navigate = useNavigate();

  return (
    <div className="d-flex flex-column min-vh-100 bg-light">
      <Navbar bg="white" expand="md" className="border-bottom shadow-sm sticky-top">
        <Container>
          <Navbar.Brand as={Link} to="/" className="d-flex align-items-center gap-2 fw-bold">
            <span className="d-inline-flex align-items-center justify-content-center bg-primary text-white rounded" style={{ width: 32, height: 32 }}>
              <FeatherIcon icon="shopping-bag" size={18} />
            </span>
            Marketplace
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="store-nav" />
          <Navbar.Collapse id="store-nav">
            <Nav className="me-auto">
              <Nav.Link as={NavLink} to="/" end>
                Home
              </Nav.Link>
              <Nav.Link as={NavLink} to="/products">
                Products
              </Nav.Link>
            </Nav>
            <Nav className="align-items-md-center gap-md-2">
              <Button as={Link} to="/cart" variant="outline-primary" size="sm" className="position-relative">
                <FeatherIcon icon="shopping-cart" size={16} />
                <span className="ms-1">Cart</span>
                {count > 0 && (
                  <Badge bg="primary" pill className="position-absolute top-0 start-100 translate-middle">
                    {count}
                  </Badge>
                )}
              </Button>
              {isAuthenticated ? (
                <Dropdown align="end">
                  <Dropdown.Toggle size="sm" variant="light" id="acct">
                    <FeatherIcon icon="user" size={16} className="me-1" />
                    {user?.first_name || user?.email?.split('@')[0] || 'Account'}
                  </Dropdown.Toggle>
                  <Dropdown.Menu>
                    <Dropdown.ItemText className="small text-muted">{user?.email}</Dropdown.ItemText>
                    <Dropdown.Divider />
                    <Dropdown.Item as={Link} to="/account">
                      My orders
                    </Dropdown.Item>
                    <Dropdown.Item as={Link} to="/admin">
                      Admin console
                    </Dropdown.Item>
                    <Dropdown.Divider />
                    <Dropdown.Item onClick={() => { logout(); navigate('/'); }}>Sign out</Dropdown.Item>
                  </Dropdown.Menu>
                </Dropdown>
              ) : (
                <>
                  <Button as={Link} to="/login" variant="link" size="sm" className="text-decoration-none">
                    Sign in
                  </Button>
                  <Button as={Link} to="/register" variant="primary" size="sm">
                    Sign up
                  </Button>
                </>
              )}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <main className="flex-grow-1 py-4">
        <Container>
          <Suspense fallback={<Loader />}>
            <Outlet />
          </Suspense>
        </Container>
      </main>

      <footer className="border-top bg-white py-3 mt-auto">
        <Container className="d-flex justify-content-between small text-muted">
          <span>© Marketplace — multi-tenant demo</span>
          <Link to="/admin" className="text-decoration-none">
            Seller / Admin
          </Link>
        </Container>
      </footer>
    </div>
  );
}
