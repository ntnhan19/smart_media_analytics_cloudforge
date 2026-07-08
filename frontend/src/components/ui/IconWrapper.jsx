import PropTypes from 'prop-types';
import * as icons from 'lucide-react';

export default function IconWrapper({ name, size = 24, color = 'currentColor', className = '' }) {
  const LucideIcon = icons[name];
  if (!LucideIcon) return null;
  return <LucideIcon size={size} color={color} className={className} />;
}

IconWrapper.propTypes = {
  name: PropTypes.string.isRequired,
  size: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  color: PropTypes.string,
  className: PropTypes.string,
};
