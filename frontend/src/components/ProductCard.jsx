import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Button, Card } from 'react-bootstrap';

import { onImgError, productImage } from 'utils/media';

export default function ProductCard({ product }) {
  return (
    <Card className="h-100 border-0 shadow-sm product-card">
      <Link to={`/product/${product.id}`} className="text-decoration-none text-reset">
        <div className="media-box ratio-4x3">
          <img src={productImage(product)} alt={product.name} onError={onImgError(product.id)} loading="lazy" />
        </div>
        <Card.Body className="pb-2">
          <Card.Title className="h6 mb-1 text-truncate">{product.name}</Card.Title>
          <div className="price-tag">{product.price ? `${product.price} ${product.currency}` : '—'}</div>
        </Card.Body>
      </Link>
      <Card.Footer className="bg-white border-0 pt-0">
        <Button as={Link} to={`/product/${product.id}`} variant="outline-primary" size="sm" className="w-100">
          View product
        </Button>
      </Card.Footer>
    </Card>
  );
}

ProductCard.propTypes = { product: PropTypes.object.isRequired };
