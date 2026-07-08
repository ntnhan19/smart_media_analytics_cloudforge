import PropTypes from 'prop-types';

export default function ScoreBadge({ score }) {
  const colorClass = score >= 0.85
    ? 'bg-sma-green text-black'
    : score >= 0.6
      ? 'bg-yellow-400 text-black'
      : 'bg-red-500 text-white';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${colorClass}`}>
      {score.toFixed(2)}
    </span>
  );
}

ScoreBadge.propTypes = {
  score: PropTypes.number.isRequired,
};
