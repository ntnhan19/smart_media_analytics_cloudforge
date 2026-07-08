
export default function DetectMoreScenesButton({ onClick, isLoading }) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className="w-full mt-4 py-[16px] bg-[#7B5CF5] hover:bg-purple-600 border border-[#7B5CF5] rounded-[6px] transition-all focus:outline-none flex items-center justify-center gap-2"
    >
      {isLoading ? (
        <>
          <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          <span className="font-inter font-bold text-[20px] leading-[24px] text-white">DETECTING...</span>
        </>
      ) : (
        <span className="font-inter font-bold text-[20px] leading-[24px] text-white">DETECH MORE SCENES +</span>
      )}
    </button>
  );
}
