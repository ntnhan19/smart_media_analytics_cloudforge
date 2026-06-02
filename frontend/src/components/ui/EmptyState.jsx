export default function EmptyState({ message }) {
  return (
    <div className="text-gray-500 text-center p-12 border border-dashed border-gray-800 rounded-lg">
      {message || 'No data found.'}
    </div>
  );
}
