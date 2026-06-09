import React from 'react';
import PropTypes from 'prop-types';

export default function ScoreBadge({ score }) {
  let colorClass = '';
  if (score >= 0.85) {
    colorClass = 'bg-sma-green text-black';
  } else if (score >= 0.6) {
    colorClass = 'bg-yellow-400 text-black';
  } else {
    colorClass = 'bg-red-500 text-white';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${colorClass}`}>
      {score.toFixed(2)}
    </span>
  );
}

ScoreBadge.propTypes = {
  score: PropTypes.number.isRequired,
};
