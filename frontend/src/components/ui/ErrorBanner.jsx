export default function ErrorBanner({ message }) {
  return (
    <div className="bg-red-500/10 text-red-500 border border-red-500/20 p-4 rounded-lg my-4">
      {message || 'An error occurred.'}
    </div>
  );
}
