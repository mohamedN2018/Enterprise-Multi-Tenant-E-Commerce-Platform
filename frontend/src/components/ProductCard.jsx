import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Card } from 'react-bootstrap';

import StarRating from 'components/StarRating';
import { onImgError, productImage } from 'utils/media';

export default function ProductCard({ product }) {
  const price = Number(product.price);
  const compare = product.compare_at_price ? Number(product.compare_at_price) : 0;
  const onSale = compare > price && price > 0;
  const off = onSale ? Math.round((1 - price / compare) * 100) : 0;

  return (
    <Card as={Link} to={`/product/${product.id}`} className="h-100 text-decoration-none text-reset product-card">
      <div className="media-box ratio-4x3">
        {onSale && <span className="sale-badge">-{off}%</span>}
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
        <div className="mt-auto d-flex align-items-baseline gap-2">
          <span className="price-tag fs-6">{product.price ? `${product.price} ${product.currency}` : '—'}</span>
          {onSale && <span className="text-muted text-decoration-line-through small">{product.compare_at_price}</span>}
        </div>
      </Card.Body>
    </Card>
  );
}

ProductCard.propTypes = { product: PropTypes.object.isRequired };
