import { Button, Dropdown, Form } from 'react-bootstrap';

import { useAuth } from 'contexts/AuthContext';
import { useStore } from 'contexts/StoreContext';

// A slim global action bar: active-store selector + signed-in user + logout.
export default function TopActions() {
  const { user, logout } = useAuth();
  const { stores, activeId, selectStore } = useStore();

  return (
    <div className="d-flex align-items-center justify-content-end gap-2 mb-3 flex-wrap">
      <span className="text-muted small">Store</span>
      <Form.Select
        size="sm"
        style={{ maxWidth: 220 }}
        value={activeId || ''}
        onChange={(e) => selectStore(e.target.value)}
      >
        {stores.length === 0 && <option value="">No stores</option>}
        {stores.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </Form.Select>

      <Dropdown align="end">
        <Dropdown.Toggle size="sm" variant="light" id="user-menu">
          {user?.email || 'Account'}
        </Dropdown.Toggle>
        <Dropdown.Menu>
          <Dropdown.ItemText className="small text-muted">{user?.email}</Dropdown.ItemText>
          <Dropdown.Divider />
          <Dropdown.Item as="div">
            <Button variant="link" className="p-0 text-danger" onClick={logout}>
              Sign out
            </Button>
          </Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown>
    </div>
  );
}
