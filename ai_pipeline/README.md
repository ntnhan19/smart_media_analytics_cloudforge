# 🤖 AI Pipeline Module

Comprehensive AI processing pipeline for video analysis, combining multimodal vision models, automatic speech recognition (ASR), scene detection, and semantic search indexing.

**Optimized for local inference on GTX 1650 (4GB VRAM)** with strategic model quantization, sequential processing, and memory management.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Module Structure](#module-structure)
- [Core Components](#core-components)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Performance Tuning](#performance-tuning)
- [Testing](#testing)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The `ai_pipeline` module orchestrates the complete video analysis workflow:

```
Video Input
    ↓
[Video Processing] → Extract metadata, create proxy
    ↓
[Scene Detection] → Identify scene boundaries
    ↓
[Audio Extraction] → Extract audio track
    ↓
[ASR/Transcription] → WhisperX for speech-to-text
    ↓
[Keyframe Extraction] → Extract frames from scene boundaries
    ↓
[Vision Analysis] → Qwen-VL + Florence-2 image understanding
    ↓
[LLM Refinement] → Structure and merge analysis outputs
    ↓
[Embedding Generation] → BGE-M3 semantic embeddings
    ↓
[Vector Storage] → ChromaDB for similarity search
    ↓
[Database Storage] → PostgreSQL for metadata
```

---

## 📁 Module Structure

```
ai_pipeline/
├── __init__.py
│
├── audio/
│   ├── __init__.py
│   └── transcriber.py          # WhisperX ASR implementation
│
├── vision/
│   ├── __init__.py
│   ├── vision_models.py        # Qwen-VL, Florence-2, ModelManager
│   └── prompt_engine.py        # Centralized prompt management
│
├── embeddings/
│   ├── __init__.py
│   └── embedding_models.py     # BGE-M3, Reranker, EmbeddingManager
│
├── models/
│   ├── __init__.py
│   └── refinement_llm.py       # Qwen2-1.5B-Instruct refinement
│
├── scene_detection/
│   ├── __init__.py
│   └── scene_detector.py       # PySceneDetect integration
│
├── ingestion/
│   ├── __init__.py
│   └── video_pipeline.py       # Main orchestration pipeline
│
└── tests/
    ├── __init__.py
    ├── test_transcriber.py     # Transcriber unit & integration tests
    ├── test_vision_tagger.py   # Vision model tests
    └── test_scene_detector_1.py  # Scene detection tests
```

---

## 🔧 Core Components

### 1. **Audio Processing** (`audio/transcriber.py`)

**WhisperX** speech-to-text with word-level timestamps.

```python
from ai_pipeline.audio.transcriber import WhisperXModel

transcriber = WhisperXModel(model_size="base", device="cuda")

result = transcriber.transcribe(
    audio_path=Path("video.mp3"),
    language="en",
    batch_size=16
)

# Result structure:
# {
#     "segments": [...],        # Segment-level timing & text
#     "words": [...],           # Word-level timing & confidence
#     "text": "Full transcript",
#     "language": "en"
# }
```

**Key Features:**
- ✅ Word-level timestamp alignment
- ✅ Automatic language detection
- ✅ 4 model sizes: tiny, base, small, medium, large
- ✅ Batch processing support
- ✅ CUDA/CPU device support

**Models:**
- `tiny` — 39M params, fastest, lower accuracy
- `base` — 74M params, recommended for most use cases
- `small` — 244M params, better accuracy
- `medium` — 769M params, high accuracy (requires more VRAM)

---

### 2. **Vision Models** (`vision/vision_models.py`)

**Qwen2.5-VL-2B-Instruct** and **Florence-2-Base** with 4-bit quantization.

```python
from ai_pipeline.vision.vision_models import QwenVLModel, Florence2Model

# Initialize Qwen-VL
qwen = QwenVLModel(model_name="Qwen/Qwen2.5-VL-2B-Instruct", device="cuda")

# Analyze image
result = qwen.analyze_image(
    image=Image.open("frame.jpg"),
    prompt="Describe this landscape in detail",
    max_new_tokens=512,
    temperature=0.3
)

# Initialize Florence-2
florence = Florence2Model(model_name="microsoft/Florence-2-base", device="cuda")

# Get detailed captions
caption = florence.caption(image, prompt="<DETAILED_CAPTION>")
```

**VRAM Optimization:**
- 4-bit NF4 quantization
- Sequential inference (batch_size=1)
- Image resize to 448px
- `torch.inference_mode()` instead of `no_grad()`
- `gc.collect() + torch.cuda.empty_cache()` after each inference

**ModelManager** for sequential loading:
```python
from ai_pipeline.vision.vision_models import ModelManager

manager = ModelManager()
manager.load_models_for_mode("balanced")

# Models loaded:
manager.qwen_vl  # Available
manager.florence # Available based on mode

# Unload to free VRAM
manager.unload_qwen_vl()  # For switching models
```

---

### 3. **Prompt Engine** (`vision/prompt_engine.py`)

Centralized prompt management for vision models, optimized for landscape, portrait, and general video analysis.

```python
from ai_pipeline.vision.prompt_engine import PromptEngine, PromptMode

# Get prompts by type
landscape_prompt = PromptEngine.PROMPTS["landscape_detail"]
portrait_prompt = PromptEngine.PROMPTS["portrait_detail"]

# Customizable prompts with structured output
# Covers: scene type, lighting, composition, colors, search tags, editor notes
```

**Available Prompt Types:**
- `landscape_detail` — Mountain scenery, nature photography
- `portrait_detail` — People, fashion, expressions
- `motion_detail` — Camera movement, action analysis
- `color_detail` — Color grading, palette analysis

---

### 4. **Embedding Models** (`embeddings/embedding_models.py`)

**BGE-M3** semantic embeddings and **BGE-Reranker-V2** for search ranking.

```python
from ai_pipeline.embeddings.embedding_models import EmbeddingManager

# Initialize
embeddings = EmbeddingManager()
embeddings.load_all()  # Load embedding model + reranker

# Encode texts
vectors = embeddings.encode(
    texts=["landscape with mountains", "people in discussion"],
    batch_size=4
)

# Rerank search results
reranked = embeddings.rerank(
    query="mountain scenery at sunset",
    documents=[doc1, doc2, doc3],
    top_k=5
)
```

**Why CPU for embeddings:**
- BGE-M3 embedding generation is CPU-efficient
- Avoids contending with VRAM for vision/LLM models
- <100ms per query on modern CPUs
- Batch processing handles throughput

---

### 5. **LLM Refinement** (`models/refinement_llm.py`)

**Qwen2-1.5B-Instruct** for structuring and merging vision model outputs.

```python
from ai_pipeline.models.refinement_llm import RefinementLLM

refiner = RefinementLLM(model_name="Qwen/Qwen2-1.5B-Instruct")

refined = refiner.refine_analysis(
    vision_outputs={
        "qwen_vl": "Detailed landscape analysis from Qwen...",
        "florence": "Caption from Florence...",
    },
    timestamp=45.5,
    scene_id=3,
    temperature=0.1  # Low temp for stable JSON
)

# Output: Structured JSON with confidence scores
```

---

### 6. **Scene Detection** (`scene_detection/scene_detector.py`)

**PySceneDetect** for frame-accurate scene boundary detection.

```python
from ai_pipeline.scene_detection.scene_detector import SceneDetector

detector = SceneDetector(
    threshold=27.0,  # 0-27, lower = more sensitive
    thumbnails_dir=Path("./thumbnails")
)

scenes = detector.detect_scenes(video_path=Path("video.mp4"))

# Returns list of (start_time, end_time) tuples
# Plus extracted keyframes for each scene
```

---

### 7. **Video Pipeline Orchestration** (`ingestion/video_pipeline.py`)

Main entry point coordinating all components.

```python
from ai_pipeline.ingestion.video_pipeline import VideoAnalysisPipeline

# Initialize with processing mode
pipeline = VideoAnalysisPipeline(processing_mode="balanced")

# Process entire video
result = pipeline.process_video(
    video_path=Path("video.mp4"),
    video_id="vid_001"  # Optional, auto-generated if not provided
)

print(result)
# {
#     'video_id': 'vid_001',
#     'status': 'success',
#     'stats': {
#         'duration_sec': 120.5,
#         'num_scenes': 15,
#         'num_frames': 45,
#         'transcript_length': 850,
#         'total_embeddings': 45,
#         ...
#     }
# }
```

---

## 🚀 Getting Started

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../backend/requirements.txt

# For development with tests
pip install pytest pytest-asyncio pytest-cov
```

### Quick Start Example

```python
from pathlib import Path
from ai_pipeline.ingestion.video_pipeline import VideoAnalysisPipeline

# Initialize pipeline
pipeline = VideoAnalysisPipeline(processing_mode="balanced")

# Process video
result = pipeline.process_video(
    video_path=Path("sample_video.mp4"),
    video_id="sample_001"
)

if result['status'] == 'success':
    print(f"✓ Video processed successfully!")
    print(f"  - {result['stats']['num_scenes']} scenes detected")
    print(f"  - {result['stats']['num_frames']} keyframes extracted")
    print(f"  - {len(result['stats']['transcript_words'])} words transcribed")
else:
    print(f"✗ Error: {result['error']}")
```

---

## ⚙️ Configuration

### Processing Modes

| Mode | Qwen-VL | Florence-2 | LLM Refinement | Frames/Scene | Use Case |
|------|---------|-----------|----------------|-------------|----------|
| `fast` | ✓ | ✗ | ✗ | 1 | Quick preview |
| `balanced` | ✓ | ✗ | ✓ | 3 | Default, good balance |
| `high` | ✓ | ✓ | ✓ | 3 | High quality |
| `ultra` | ✓ | ✓ (sequential) | ✓ | 5 | Maximum quality, slowest |

### Environment Variables

Create `.env` file (or copy from `.env.example`):

```dotenv
# Vision Models
QWEN_VL_MODEL=Qwen/Qwen2.5-VL-2B-Instruct
VISION_MODEL_DEVICE=cuda
FLORENCE_MODEL=microsoft/Florence-2-base

# ASR
WHISPER_MODEL=base
WHISPER_DEVICE=cuda

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu

# Processing
PROCESSING_MODE=balanced
FRAMES_PER_SCENE=3
USE_REFINEMENT=true
```

---

## 💡 Usage Examples

### Example 1: Basic Video Analysis

```python
from pathlib import Path
from ai_pipeline.ingestion.video_pipeline import VideoAnalysisPipeline

pipeline = VideoAnalysisPipeline(processing_mode="fast")
result = pipeline.process_video(Path("landscape.mp4"))
```

### Example 2: Custom Transcription

```python
from ai_pipeline.audio.transcriber import WhisperXModel

transcriber = WhisperXModel(model_size="base")
result = transcriber.transcribe(
    Path("audio.mp3"),
    language="en"
)

for word in result['words']:
    print(f"{word['word']}: {word['start']:.2f}s - {word['end']:.2f}s")
```

### Example 3: Image Analysis with Custom Prompt

```python
from PIL import Image
from ai_pipeline.vision.vision_models import QwenVLModel
from ai_pipeline.vision.prompt_engine import PromptEngine

model = QwenVLModel()
image = Image.open("frame.jpg")

prompt = PromptEngine.PROMPTS["landscape_detail"]
analysis = model.analyze_image(image, prompt=prompt)
print(analysis)
```

### Example 4: Semantic Search Setup

```python
from ai_pipeline.embeddings.embedding_models import EmbeddingManager

embeddings = EmbeddingManager()
embeddings.load_all()

# Index documents
texts = ["Mountain landscape at sunset", "Group of people talking", ...]
vectors = embeddings.encode(texts)

# Search
query = "scenic mountain views"
query_vector = embeddings.encode([query])[0]
# Use query_vector for similarity search in ChromaDB
```

---

## 🎯 Performance Tuning

### For GTX 1650 (4GB VRAM)

1. **Use 4-bit Quantization**
   ```python
   # Automatically used in QwenVLModel, RefinementLLM
   # ~1.5-2GB VRAM per model with quantization
   ```

2. **Sequential Model Loading**
   ```python
   manager.load_qwen_vl()
   # Do analysis
   manager.unload_qwen_vl()
   manager.load_florence()  # Now have space for Florence
   ```

3. **Image Resizing**
   ```python
   # Automatically done in _resize_image()
   # Reduces tokenization overhead
   max_size = 448  # pixels
   ```

4. **Batch Processing**
   ```python
   # Process frames one at a time
   batch_size = 1
   ```

5. **Enable Memory Optimization**
   ```dotenv
   ENABLE_MEMORY_OPTIMIZATION=true
   DTYPE=float16
   GPU_MEMORY_FRACTION=0.9
   ```

### VRAM Estimates

| Component | Model | Quantization | VRAM |
|-----------|-------|--------------|------|
| Vision | Qwen-VL 2B | 4-bit | ~1.2GB |
| Vision | Florence 2B | float16 | ~1.8GB |
| LLM | Qwen2 1.5B | 4-bit | ~0.8GB |
| Embeddings | BGE-M3 | CPU | None |
| **Total (balanced)** | - | - | ~2.0GB |

---

## 🧪 Testing

### Run All Tests

```bash
pytest ai_pipeline/tests/ -v

# With coverage
pytest ai_pipeline/tests/ --cov=ai_pipeline --cov-report=html
```

### Run Specific Test Suite

```bash
# Test transcriber
pytest ai_pipeline/tests/test_transcriber.py -v

# Test vision models
pytest ai_pipeline/tests/test_vision_tagger.py -v

# Test scene detection
pytest ai_pipeline/tests/test_scene_detector_1.py -v
```

### Run with Performance Profiling

```bash
pytest ai_pipeline/tests/ -v --durations=10
```

---

## 📚 API Reference

### WhisperXModel

```python
class WhisperXModel:
    def __init__(self, model_size: str = "base", device: str = "cuda")
    def transcribe(
        audio_path: Path,
        language: str = None,
        batch_size: int = 16
    ) -> Dict[str, Any]
```

### QwenVLModel

```python
class QwenVLModel:
    def __init__(self, model_name: str = None, device: str = None)
    def analyze_image(
        image: Image.Image,
        prompt: str = None,
        max_new_tokens: int = None,
        temperature: float = 0.3
    ) -> str
```

### EmbeddingManager

```python
class EmbeddingManager:
    def load_embedding_model(self)
    def load_reranker_model(self)
    def load_all(self)
    def encode(texts: Union[str, List[str]]) -> np.ndarray
    def rerank(query: str, documents: List[str], top_k: int) -> List[Dict]
    def unload_all(self)
```

### VideoAnalysisPipeline

```python
class VideoAnalysisPipeline:
    def __init__(self, processing_mode: str = "fast")
    def process_video(
        video_path: Path,
        video_id: str = None
    ) -> Dict[str, Any]
```

---

## 🐛 Troubleshooting

### Out of Memory (OOM)

**Solution:**
1. Switch to `fast` mode (fewer frames, only Qwen-VL)
2. Set `IMAGE_MAX_SIZE=256` (smaller images)
3. Use CPU device: `VISION_MODEL_DEVICE=cpu`

### Model Download Issues

**Solution:**
```bash
# Pre-download models
from ai_pipeline.vision.vision_models import QwenVLModel
model = QwenVLModel()  # Downloads on first init
```

### Slow Inference

**Solution:**
1. Ensure `VISION_MODEL_DEVICE=cuda`
2. Check GPU availability: `python -c "import torch; print(torch.cuda.is_available())"`
3. Use `DTYPE=float16` for faster computation

### Audio Not Extracted

**Solution:**
1. Ensure FFmpeg is installed: `ffmpeg -version`
2. Check video codec support
3. Use proxy video mode for problematic formats

---

## 📞 Support & Contribution

- **Issues**: Report bugs or feature requests on GitHub
- **Pull Requests**: Welcome for improvements, tests, and optimizations
- **Documentation**: Update README.md with new features

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](../LICENSE) for details.

---

<p align="center">
  Built for 🎬 <strong>Smart Media Analytics</strong><br>
  Optimized for local GPU inference with strategic quantization
</p>
