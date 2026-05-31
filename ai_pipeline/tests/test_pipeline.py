"""
Test End-to-End Video Analysis Pipeline
Tự động quét và xử lý tất cả video từ ai_pipeline/videos
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from pathlib import Path
import time
import traceback

from ai_pipeline.ingestion.video_pipeline import VideoAnalysisPipeline


def main():
    """Main entry point for testing video analysis pipeline"""
    
    # Configuration
    video_dir = Path(__file__).parent.parent / "videos"
    supported_formats = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    
    print("\n" + "=" * 70)
    print("VIDEO ANALYSIS PIPELINE - END-TO-END TEST")
    print("=" * 70 + "\n")
    
    # Discover videos
    print("DISCOVERING VIDEOS...")
    print("-" * 70)
    
    video_files = []
    if video_dir.exists():
        for file_path in sorted(video_dir.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                video_files.append(file_path)
                print(f"  [OK] Found: {file_path.name}")
    
    if not video_files:
        print(f"No videos found in {video_dir}")
        return
    
    print(f"Total videos found: {len(video_files)}\n")
    
    # Initialize pipeline
    print("INITIALIZING PIPELINE...")
    print("-" * 70)
    
    try:
        pipeline = VideoAnalysisPipeline(processing_mode="fast")
        print("[OK] Pipeline initialized (mode: fast)\n")
    except Exception as e:
        print(f"[FAIL] Failed to initialize pipeline: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return
    
    # Process each video
    print("PROCESSING VIDEOS...")
    print("-" * 70 + "\n")
    
    results = []
    
    for idx, video_path in enumerate(video_files, 1):
        print(f"[{idx}/{len(video_files)}] Processing: {video_path.name}")
        
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"  File size: {file_size_mb:.2f} MB")
        
        result = {
            'name': video_path.name,
            'size_mb': file_size_mb,
            'status': 'FAIL',
            'time_sec': 0,
            'error': None
        }
        
        try:
            start_time = time.time()
            print(f"  Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Call process_video with correct signature
            # process_video(self, video_path: Path, video_id: str = None)
            process_result = pipeline.process_video(video_path=video_path)
            
            elapsed_time = time.time() - start_time
            result['time_sec'] = elapsed_time
            
            print(f"  End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Processing time: {elapsed_time:.2f}s")
            
            # Check result status
            if process_result.get('status') == 'success':
                result['status'] = 'PASS'
                print(f"  [OK] PASS")
            else:
                result['status'] = 'FAIL'
                result['error'] = process_result.get('error', 'Unknown error')
                print(f"  [FAIL] FAIL: {result['error']}")
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            result['time_sec'] = elapsed_time
            result['status'] = 'FAIL'
            result['error'] = str(e)
            
            print(f"  [ERROR] EXCEPTION: {type(e).__name__}")
            print(f"  Error: {str(e)}")
            print(f"  Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    print(f"    {line}")
        
        print()
        results.append(result)
    
    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70 + "\n")
    
    print(f"{'Video Name':<30} {'Status':<8} {'Time (s)':<12} {'Size (MB)':<12}")
    print("-" * 70)
    
    for result in results:
        name = result['name'][:28]
        status = result['status']
        time_sec = f"{result['time_sec']:.2f}"
        size_mb = f"{result['size_mb']:.2f}"
        print(f"{name:<30} {status:<8} {time_sec:<12} {size_mb:<12}")
    
    print("-" * 70 + "\n")
    
    # Calculate statistics
    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    total_time = sum(r['time_sec'] for r in results)
    
    print(f"Total videos: {len(results)}")
    print(f"[OK] PASSED: {pass_count}")
    print(f"[FAIL] FAILED: {fail_count}")
    print(f"Success rate: {(pass_count/len(results)*100):.1f}%")
    print(f"Total processing time: {total_time:.2f} seconds")
    if len(results) > 0:
        print(f"Average processing time: {(total_time/len(results)):.2f} seconds")
    print("\n" + "=" * 70 + "\n")
    
    # Print failed videos details
    failed_videos = [r for r in results if r['status'] == 'FAIL']
    if failed_videos:
        print("FAILED VIDEOS DETAILS:")
        for result in failed_videos:
            print(f"\n  {result['name']}:")
            print(f"    Error: {result['error']}")
        print()


if __name__ == "__main__":
    main()
