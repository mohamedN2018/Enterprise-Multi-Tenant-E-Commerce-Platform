// react-bootstrap
import { ListGroup, Dropdown } from 'react-bootstrap';

// third party
import FeatherIcon from 'feather-icons-react';

import { useAuth } from 'contexts/AuthContext';

// -----------------------|| NAV RIGHT ||-----------------------//

export default function NavRight() {
  const { user, logout } = useAuth();
  const name = user ? [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email : 'Account';
  const initial = (user?.first_name || user?.email || '?').charAt(0).toUpperCase();

  return (
    <ListGroup as="ul" bsPrefix=" " className="list-unstyled">
      <ListGroup.Item as="li" bsPrefix=" " className="pc-h-item">
        <Dropdown className="drp-user">
          <Dropdown.Toggle as="a" variant="link" className="pc-head-link arrow-none me-0 user-name">
            <span className="user-avatar d-inline-flex align-items-center justify-content-center bg-primary text-white rounded-circle" style={{ width: 36, height: 36 }}>
              {initial}
            </span>
            <span>
              <span className="user-name">{name}</span>
              <span className="user-desc">{user?.email}</span>
            </span>
          </Dropdown.Toggle>
          <Dropdown.Menu className="dropdown-menu-end pc-h-dropdown">
            <Dropdown.Header className="pro-head">
              <span className="text-overflow m-0">Signed in as</span>
              <h6 className="text-overflow m-0">{user?.email}</h6>
            </Dropdown.Header>
            <Dropdown.Item as="button" onClick={logout}>
              <FeatherIcon icon="log-out" className="me-2" /> Sign out
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      </ListGroup.Item>
    </ListGroup>
  );
}
