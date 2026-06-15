import React from 'react';
import PropTypes from 'prop-types';

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export default function TimestampChip({ startSec, endSec }) {
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sma-surface text-white border border-gray-700">
      {formatTime(startSec)} &rarr; {formatTime(endSec)}
    </span>
  );
}

TimestampChip.propTypes = {
  startSec: PropTypes.number.isRequired,
  endSec: PropTypes.number.isRequired,
};
