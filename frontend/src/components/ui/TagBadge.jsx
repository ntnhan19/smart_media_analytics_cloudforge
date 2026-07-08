import PropTypes from 'prop-types';

export default function TagBadge({ label, color = 'sma-purple' }) {
  const isHex = color.startsWith('#');
  const bgStyle = isHex ? { backgroundColor: color } : {};
  // If not hex, we assume it's a tailwind color name like 'sma-purple' or 'sma-blue'
  const bgClass = isHex ? '' : `bg-${color}`;

  return (
    <span 
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium text-white ${bgClass}`}
      style={bgStyle}
    >
      {label}
    </span>
  );
}

TagBadge.propTypes = {
  label: PropTypes.string.isRequired,
  color: PropTypes.string,
};
