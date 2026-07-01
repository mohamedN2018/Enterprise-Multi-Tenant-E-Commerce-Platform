import PropTypes from 'prop-types';
import FeatherIcon from 'feather-icons-react';

// Star rating: read-only display, or interactive when `onChange` is provided.
export default function StarRating({ value = 0, count, size = 16, onChange, className = '' }) {
  const rounded = Math.round(value);
  return (
    <span className={`d-inline-flex align-items-center ${className}`} style={{ gap: 2 }}>
      {[1, 2, 3, 4, 5].map((s) => (
        <FeatherIcon
          key={s}
          icon="star"
          size={size}
          onClick={onChange ? () => onChange(s) : undefined}
          style={{
            cursor: onChange ? 'pointer' : 'default',
            fill: s <= rounded ? '#f59e0b' : 'none',
            color: '#f59e0b'
          }}
        />
      ))}
      {count != null && <span className="text-muted small ms-1">({count})</span>}
    </span>
  );
}

StarRating.propTypes = {
  value: PropTypes.number,
  count: PropTypes.number,
  size: PropTypes.number,
  onChange: PropTypes.func,
  className: PropTypes.string
};
