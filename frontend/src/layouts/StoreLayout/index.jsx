import { Suspense, useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Badge, Button, Container, Dropdown, Form, InputGroup, Nav, Navbar } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';
import Loader from 'components/Loader/Loader';

export default function StoreLayout() {
  const { isAuthenticated, user, logout } = useAuth();
  const { count } = useCart();
  const navigate = useNavigate();
  const [q, setQ] = useState('');

  const search = (e) => {
    e.preventDefault();
    navigate(q.trim() ? `/products?search=${encodeURIComponent(q.trim())}` : '/products');
  };

  return (
    <div className="sf-app d-flex flex-column min-vh-100">
      <Navbar expand="lg" className="sf-navbar sticky-top py-2">
        <Container>
          <Navbar.Brand as={Link} to="/" className="d-flex align-items-center gap-2 fw-bold me-3">
            <span className="d-inline-flex align-items-center justify-content-center bg-primary text-white rounded" style={{ width: 32, height: 32 }}>
              <FeatherIcon icon="shopping-bag" size={18} />
            </span>
            Marketplace
          </Navbar.Brand>

          <Form className="sf-search d-none d-lg-flex flex-grow-1 me-3" style={{ maxWidth: 460 }} onSubmit={search}>
            <InputGroup>
              <Form.Control placeholder="Search products…" value={q} onChange={(e) => setQ(e.target.value)} />
              <InputGroup.Text role="button" onClick={search}>
                <FeatherIcon icon="search" size={16} />
              </InputGroup.Text>
            </InputGroup>
          </Form>

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
            <Form className="sf-search d-lg-none my-2" onSubmit={search}>
              <InputGroup>
                <Form.Control placeholder="Search products…" value={q} onChange={(e) => setQ(e.target.value)} />
                <InputGroup.Text role="button" onClick={search}>
                  <FeatherIcon icon="search" size={16} />
                </InputGroup.Text>
              </InputGroup>
            </Form>
            <Nav className="align-items-lg-center gap-lg-2">
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
                      My account
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

      <footer className="sf-footer mt-auto pt-5 pb-4">
        <Container>
          <div className="row g-4">
            <div className="col-lg-4">
              <div className="d-flex align-items-center gap-2 fw-bold text-white mb-2">
                <span className="d-inline-flex align-items-center justify-content-center bg-primary rounded" style={{ width: 30, height: 30 }}>
                  <FeatherIcon icon="shopping-bag" size={16} />
                </span>
                Marketplace
              </div>
              <p className="small mb-0" style={{ maxWidth: 320 }}>
                A multi-tenant marketplace demo — independent stores, one checkout. Built with Django & React.
              </p>
            </div>
            <div className="col-6 col-lg-2">
              <h6 className="mb-3">Shop</h6>
              <ul className="list-unstyled small d-grid gap-2 mb-0">
                <li><Link to="/products">All products</Link></li>
                <li><Link to="/">Stores</Link></li>
                <li><Link to="/cart">Cart</Link></li>
              </ul>
            </div>
            <div className="col-6 col-lg-2">
              <h6 className="mb-3">Account</h6>
              <ul className="list-unstyled small d-grid gap-2 mb-0">
                <li><Link to="/account">My orders</Link></li>
                <li><Link to="/account">Wishlist</Link></li>
                <li><Link to="/login">Sign in</Link></li>
              </ul>
            </div>
            <div className="col-lg-2">
              <h6 className="mb-3">Sellers</h6>
              <ul className="list-unstyled small d-grid gap-2 mb-0">
                <li><Link to="/admin">Seller / Admin</Link></li>
              </ul>
            </div>
          </div>
          <hr className="border-secondary my-4" />
          <div className="small d-flex flex-wrap justify-content-between gap-2">
            <span>© Marketplace — multi-tenant demo</span>
            <span>Demo checkout — no real payments.</span>
          </div>
        </Container>
      </footer>
    </div>
  );
}
