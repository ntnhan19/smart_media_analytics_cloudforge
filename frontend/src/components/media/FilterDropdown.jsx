import PropTypes from 'prop-types';
import { Icon } from '@iconify/react';

export default function FilterDropdown({ options, selected, onChange, label, className }) {
  return (
    <div className={`relative flex items-center h-[26px] border border-sma-purple rounded-[8px] bg-transparent hover:bg-sma-purple/10 transition-colors ${className}`}>
      <select
        className="appearance-none bg-transparent text-white text-[10px] leading-[12px] font-inter uppercase w-full h-full px-[10px] pr-[24px] outline-none cursor-pointer"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
      >
        {label && <option value="" disabled>{label}</option>}
        {options.map((option) => (
          <option key={option} value={option} className="bg-sma-surface text-white">
            {option}
          </option>
        ))}
      </select>
      <Icon 
        icon="tabler:chevron-down" 
        width="14" 
        height="14" 
        className="text-white absolute right-[6px] pointer-events-none" 
      />
    </div>
  );
}

FilterDropdown.propTypes = {
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  selected: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  label: PropTypes.string,
  className: PropTypes.string
};
