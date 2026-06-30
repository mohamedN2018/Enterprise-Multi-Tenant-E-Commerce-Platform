// react-bootstrap
import { ListGroup, Dropdown } from 'react-bootstrap';

// third party
import FeatherIcon from 'feather-icons-react';

import { useStore } from 'contexts/StoreContext';

// -----------------------|| NAV LEFT — active store selector ||-----------------------//

export default function NavLeft() {
  const { stores, activeStore, selectStore } = useStore();

  return (
    <ListGroup as="ul" bsPrefix=" " className="list-unstyled">
      <Dropdown as="li" className="pc-h-item">
        <Dropdown.Toggle as="a" variant="link" className="pc-head-link arrow-none me-0">
          <FeatherIcon icon="shopping-bag" className="me-2" />
          <span>{activeStore ? activeStore.name : 'No store'}</span>
          <FeatherIcon icon="chevron-down" className="ms-1" size={16} />
        </Dropdown.Toggle>
        <Dropdown.Menu className="pc-h-dropdown">
          {stores.length === 0 && <Dropdown.ItemText className="text-muted">No stores available</Dropdown.ItemText>}
          {stores.map((s) => (
            <Dropdown.Item key={s.id} active={activeStore?.id === s.id} onClick={() => selectStore(s.id)}>
              <i className="material-icons-two-tone">storefront</i>
              <span>{s.name}</span>
            </Dropdown.Item>
          ))}
        </Dropdown.Menu>
      </Dropdown>
    </ListGroup>
  );
}
