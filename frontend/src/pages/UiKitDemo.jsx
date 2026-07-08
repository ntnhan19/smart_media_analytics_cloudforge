import Button from '../components/ui/Button';
import IconWrapper from '../components/ui/IconWrapper';
import TagBadge from '../components/ui/TagBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import ScoreBadge from '../components/ui/ScoreBadge';
import TimestampChip from '../components/ui/TimestampChip';

export default function UiKitDemo() {
  return (
    <div className="min-h-screen bg-sma-bg text-white p-8 font-sans">
      <h1 className="text-3xl font-bold mb-8">UI Kit Demo</h1>

      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">Buttons</h2>
        <div className="flex gap-4 items-center">
          <Button label="Primary Button" onClick={() => console.log('Primary')} variant="primary" />
          <Button label="Secondary Button" onClick={() => console.log('Secondary')} variant="secondary" />
          <Button label="Disabled" onClick={() => {}} disabled />
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">IconWrapper (Lucide)</h2>
        <div className="flex gap-4 items-center bg-sma-surface p-4 rounded-lg">
          <IconWrapper name="Home" size={24} className="text-sma-purple" />
          <IconWrapper name="Settings" size={32} className="text-sma-blue" />
          <IconWrapper name="User" size={24} color="#4ADE80" />
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">TagBadge</h2>
        <div className="flex gap-4 items-center">
          <TagBadge label="Default Purple" />
          <TagBadge label="Custom Blue" color="sma-blue" />
          <TagBadge label="Hex Color" color="#f59e0b" />
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">LoadingSpinner</h2>
        <div className="bg-sma-surface p-4 rounded-lg inline-block">
          <LoadingSpinner />
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">EmptyState</h2>
        <div className="max-w-md">
          <EmptyState
            icon={<IconWrapper name="FolderOpen" size={48} />}
            title="Your Library is Empty"
            description="Upload your first media file to start analyzing."
            action={<Button label="Upload for the 1st" onClick={() => console.log('Upload')} />}
          />
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">ScoreBadge</h2>
        <div className="flex gap-4 items-center bg-sma-surface p-4 rounded-lg">
          <ScoreBadge score={0.95} /> {/* Green */}
          <ScoreBadge score={0.75} /> {/* Yellow */}
          <ScoreBadge score={0.45} /> {/* Red */}
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">TimestampChip</h2>
        <div className="flex gap-4 items-center bg-sma-surface p-4 rounded-lg">
          <TimestampChip startSec={142.5} endSec={161.2} /> {/* 02:22 -> 02:41 */}
          <TimestampChip startSec={0} endSec={45.8} /> {/* 00:00 -> 00:45 */}
        </div>
      </section>
    </div>
  );
}
