import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Card, Col, Nav, Row } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

import { useAuth } from 'contexts/AuthContext';
import { useCart } from 'contexts/CartContext';
import OrdersTab from './account/OrdersTab';
import WishlistTab from './account/WishlistTab';
import AddressesTab from './account/AddressesTab';
import RewardsTab from './account/RewardsTab';

const TABS = [
  { key: 'orders', label: 'Orders', icon: 'package', Comp: OrdersTab },
  { key: 'wishlist', label: 'Wishlist', icon: 'heart', Comp: WishlistTab },
  { key: 'addresses', label: 'Addresses', icon: 'map-pin', Comp: AddressesTab },
  { key: 'rewards', label: 'Wallet & Rewards', icon: 'gift', Comp: RewardsTab }
];

export default function Account() {
  const { isAuthenticated, user } = useAuth();
  const { shopStore } = useCart();
  const [active, setActive] = useState('orders');

  if (!isAuthenticated) {
    return (
      <Alert variant="info">
        Please <Link to="/login">sign in</Link> to view your account.
      </Alert>
    );
  }
  if (!shopStore) {
    return (
      <Alert variant="info">
        Start shopping to build your account. <Link to="/products">Browse products →</Link>
      </Alert>
    );
  }

  const current = TABS.find((t) => t.key === active) || TABS[0];
  const ActiveComp = current.Comp;

  return (
    <>
      <h3 className="fw-bold mb-3">My account</h3>
      <Row className="g-4">
        <Col md={3}>
          <Card className="border-0 shadow-sm">
            <Card.Body>
              <div className="fw-semibold text-truncate">{user?.email}</div>
              <div className="text-muted small mb-3">Shopping at {shopStore.name}</div>
              <Nav className="flex-column account-nav">
                {TABS.map((t) => (
                  <Nav.Link key={t.key} active={active === t.key} onClick={() => setActive(t.key)} role="button">
                    <FeatherIcon icon={t.icon} size={16} /> {t.label}
                  </Nav.Link>
                ))}
              </Nav>
            </Card.Body>
          </Card>
        </Col>
        <Col md={9}>
          <Card className="border-0 shadow-sm">
            <Card.Body>
              <h5 className="fw-bold mb-3">{current.label}</h5>
              <ActiveComp store={shopStore} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
}
