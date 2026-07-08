import PropTypes from 'prop-types';

export default function Button({ label, onClick, disabled = false, variant = 'primary' }) {
  const baseClasses = 'px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-sma-bg disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-sma-purple text-white hover:bg-opacity-90 focus:ring-sma-purple',
    secondary: 'border border-sma-purple text-sma-purple hover:bg-sma-purple hover:bg-opacity-10 focus:ring-sma-purple',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variants[variant]}`}
    >
      {label}
    </button>
  );
}

Button.propTypes = {
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  variant: PropTypes.oneOf(['primary', 'secondary']),
};
