import { Link } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import FeatherIcon from 'feather-icons-react';

export default function NotFound() {
  return (
    <div className="text-center py-5">
      <div className="display-1 fw-bold text-primary">404</div>
      <h4 className="mb-2">Page not found</h4>
      <p className="text-muted mb-4">The page you&apos;re looking for doesn&apos;t exist or has moved.</p>
      <Button as={Link} to="/" variant="primary">
        <FeatherIcon icon="home" size={16} className="me-1" /> Back to the marketplace
      </Button>
    </div>
  );
}
