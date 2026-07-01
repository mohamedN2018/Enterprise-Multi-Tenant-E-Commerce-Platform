import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Card } from 'react-bootstrap';

import StarRating from 'components/StarRating';
import { onImgError, productImage } from 'utils/media';

export default function ProductCard({ product }) {
  return (
    <Card as={Link} to={`/product/${product.id}`} className="h-100 text-decoration-none text-reset product-card">
      <div className="media-box ratio-4x3">
        <img src={productImage(product)} alt={product.name} onError={onImgError(product.id)} loading="lazy" />
      </div>
      <Card.Body className="d-flex flex-column p-3">
        <div className="fw-semibold text-truncate mb-1">{product.name}</div>
        {product.review_count > 0 ? (
          <div className="mb-1">
            <StarRating value={product.rating} count={product.review_count} size={13} />
          </div>
        ) : (
          <div className="small text-muted mb-1">No reviews yet</div>
        )}
        <div className="price-tag fs-6 mt-auto">
          {product.price ? `${product.price} ${product.currency}` : '—'}
        </div>
      </Card.Body>
    </Card>
  );
}

ProductCard.propTypes = { product: PropTypes.object.isRequired };
