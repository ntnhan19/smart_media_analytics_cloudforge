
export default function MatchBadge({ score }) {
  let colorClass = 'bg-gray-800 text-gray-300 border-gray-700';
  
  if (score >= 0.85) {
    colorClass = 'bg-green-900/30 text-green-400 border-green-800/50';
  } else if (score >= 0.6) {
    colorClass = 'bg-yellow-900/30 text-yellow-400 border-yellow-800/50';
  } else if (score < 0.6 && score > 0) {
    colorClass = 'bg-red-900/30 text-red-400 border-red-800/50';
  }

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${colorClass}`}>
      {Math.round(score * 100)}% Match
    </span>
  );
}
