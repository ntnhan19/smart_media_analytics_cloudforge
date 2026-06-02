import HealthCheck from '../components/ui/HealthCheck';

export default function Dashboard() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="bg-gray-900 px-4 py-2 rounded-full border border-gray-800">
          <HealthCheck />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
          <h3 className="text-gray-400 font-medium">Total Assets</h3>
          <p className="text-4xl font-bold mt-2">0</p>
        </div>
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
          <h3 className="text-gray-400 font-medium">Storage Used</h3>
          <p className="text-4xl font-bold mt-2">0 MB</p>
        </div>
        <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
          <h3 className="text-gray-400 font-medium">Recent Searches</h3>
          <p className="text-4xl font-bold mt-2">0</p>
        </div>
      </div>
    </div>
  );
}
