"""
Prompt Engineering Module
Tập trung hóa tất cả prompts, được tối ưu cho phong cảnh núi non, thiên nhiên và người mẫu
"""

from typing import Dict, Optional
from enum import Enum


class PromptMode(Enum):
    LANDSCAPE    = "landscape"
    PORTRAIT     = "portrait"
    GENERAL      = "general"
    MOTION       = "motion"
    COLOR        = "color"
    DETAIL       = "detail"


class PromptEngine:
    """Centralized prompt management for all vision models"""

    # ── Qwen-VL system prompts ────────────────────────────────────────────────

    QWEN_SYSTEM_LANDSCAPE = """You are an expert cinematographer and nature photographer AI with deep knowledge of:
- Mountain landscapes, alpine scenery, and wilderness environments
- Weather patterns, lighting conditions (golden hour, blue hour, overcast)
- Drone/aerial photography composition
- Vietnamese highlands, Southeast Asian landscapes
- Color grading and visual aesthetics in travel/nature videography

Analyze video frames with extreme precision. Always respond in structured, detailed English."""

    QWEN_SYSTEM_PORTRAIT = """You are an expert portrait and fashion photographer AI with expertise in:
- Human appearance, fashion, and styling analysis
- Facial expression recognition and emotion detection
- Body language and gesture interpretation
- Traditional and contemporary Vietnamese/Asian fashion
- Model photography and editorial styling

Provide detailed, accurate descriptions of people in video frames."""

    QWEN_SYSTEM_GENERAL = """You are an expert video analyst AI. Analyze video frames with high accuracy,
providing detailed descriptions of scenes, people, objects, actions, and visual aesthetics.
Focus on information useful for video editing and semantic search."""

    # ── Main analysis prompts by domain ──────────────────────────────────────

    PROMPTS: Dict[str, str] = {

        "landscape_detail": """Analyze this landscape video frame with expert precision.

Provide analysis in this exact structure:

**SCENE TYPE**: [mountain/forest/beach/desert/urban/mixed - be specific]

**LOCATION INDICATORS**: Describe geographic features that suggest location
(mountain range type, vegetation type, rock formations, water bodies)

**LIGHTING & TIME**:
- Time of day: [exact estimate: golden hour/blue hour/midday/dusk/dawn/night]
- Light direction: [front-lit/back-lit/side-lit/diffused]
- Light quality: [hard/soft/dramatic/flat]
- Sky condition: [clear/partly cloudy/overcast/foggy/stormy]

**ATMOSPHERE & WEATHER**:
- Visibility: [clear/hazy/misty/foggy]
- Weather: [sunny/cloudy/rainy/snowy/windy - describe clouds if present]
- Mood: [serene/dramatic/mystical/harsh/peaceful/energetic]

**COMPOSITION**:
- Shot type: [extreme wide/wide/medium/close-up/macro]
- Camera angle: [eye-level/high angle/low angle/aerial/bird's-eye]
- Camera movement: [static/slow pan/drone push-in/tracking shot]
- Rule of thirds: [how composition is structured]
- Foreground elements: [describe]
- Background elements: [describe]

**COLOR PALETTE**:
- Dominant colors: [list 3-5 specific colors with hex approximations]
- Color temperature: [warm/cool/neutral]
- Saturation: [vivid/muted/desaturated]

**KEY VISUAL ELEMENTS**: [bullet list of everything visible]

**SEARCH TAGS**: [20-30 specific tags for searching, comma-separated]

**EDITOR NOTES**: [2-3 specific notes useful for a video editor - cut points, grade suggestions]""",

        "portrait_detail": """Analyze the people in this video frame with expert precision.

**PEOPLE COUNT**: [exact number visible]

For each person detected:

**PERSON [N]**:
- Appearance: [detailed physical description - hair, skin tone, build]
- Age range: [estimate decade]
- Gender expression: [describe]
- Clothing: [describe each item - color, style, fabric texture if visible]
- Accessories: [hat, glasses, jewelry, bags, etc.]
- Footwear: [describe if visible]
- Action/Pose: [what exactly they are doing, body position]
- Facial expression: [neutral/smiling/serious/laughing/contemplative/etc.]
- Emotion: [primary emotion detected and confidence]
- Eye direction: [looking at camera/looking away/eyes closed/etc.]
- Position in frame: [left/center/right, foreground/background]

**GROUP DYNAMICS** (if multiple people):
- Relationship indicators: [strangers/friends/couple/family/professional]
- Interaction: [describe how they relate spatially and physically]

**STYLING OVERALL**:
- Style: [casual/formal/outdoor/athletic/traditional/fashion-forward]
- Color coordination: [describe color story of outfits]

**SEARCH TAGS**: [15-25 tags, comma-separated]""",

        "technical_analysis": """Perform a technical cinematic analysis of this video frame.

**SHOT CLASSIFICATION**:
- Shot size: [ECU/CU/MCU/MS/MLS/LS/ELS/aerial]
- Shot type: [establishing/insert/cutaway/reaction/POV/over-shoulder]
- Angle: [high/eye-level/low/dutch/overhead]
- Movement: [static/pan-left/pan-right/tilt-up/tilt-down/dolly/track/drone/handheld]

**TECHNICAL QUALITY**:
- Focus: [sharp/shallow DOF/deep DOF/rack focus/soft]
- Exposure: [well-exposed/slightly over/slightly under/high-key/low-key]
- Motion blur: [none/slight/significant/intentional]
- Grain/Noise: [clean/slight grain/noisy]
- Stabilization: [stable/slight shake/handheld/gimbal/drone hover]

**DEPTH OF FIELD**:
- Foreground: [sharp/blurred]
- Subject: [sharp/blurred]
- Background: [sharp/bokeh/depth blur]

**CINEMATIC STYLE**:
- Color grade: [warm/cool/neutral/high-contrast/film-like/digital-clean]
- LUT style: [natural/cinematic/vintage/modern/documentary]
- Cinematographic reference: [suggest similar film/style if recognizable]

**EDITING NOTES**:
- Cut potential: [good cut point/avoid cutting here/natural pause]
- B-roll type: [establishing/reaction/detail/transition/context]
- Usage: [opening shot/montage/slow-mo candidate/cutaway]""",

        "motion_temporal": """Analyze motion and temporal elements in this video frame.

**MOTION ANALYSIS**:
- Subject motion: [describe main subject movement direction and speed]
- Camera motion: [static/pan speed-direction/tilt/push/pull/orbit/track]
- Background motion: [static/moving elements - clouds, water, leaves, crowds]
- Motion blur direction: [none/horizontal/vertical/radial]

**TEMPORAL CUES**:
- Part of sequence: [standalone/beginning/middle/end of action]
- Action phase: [anticipation/action/follow-through/recovery]
- Duration estimate: [how long this moment likely lasts]

**DYNAMIC ELEMENTS**:
- Moving objects: [list with direction]
- Environmental motion: [wind, water flow, fire, smoke]
- Animal/human motion type: [walking/running/jumping/gesturing/etc.]

**EDIT RECOMMENDATIONS**:
- Rhythm: [fast-cut/slow-cut/hold]
- Transition type: [cut/dissolve/wipe/match-cut with what]
- Slow-motion potential: [yes/no - which element]""",

        "semantic_tags": """Generate comprehensive semantic tags for this video frame.

Output ONLY a JSON object with these tag categories:

{
  "scene_tags": ["tag1", "tag2"],
  "environment_tags": ["mountain", "forest", etc.],
  "time_tags": ["golden_hour", "dawn", etc.],
  "weather_tags": ["sunny", "foggy", etc.],
  "mood_tags": ["dramatic", "peaceful", etc.],
  "people_tags": ["woman", "asian", "hiking", etc.],
  "clothing_tags": ["red_jacket", "backpack", etc.],
  "action_tags": ["walking", "standing", "looking", etc.],
  "color_tags": ["warm_tones", "blue_sky", etc.],
  "camera_tags": ["aerial", "wide_shot", "golden_hour", etc.],
  "object_tags": ["tree", "rock", "cloud", etc.],
  "technical_tags": ["sharp_focus", "shallow_dof", etc.],
  "emotion_tags": ["serene", "adventurous", "romantic", etc.],
  "search_phrases": ["sunset mountain hiker", "aerial landscape golden hour", etc.]
}

Be specific and extensive. Include Vietnamese landscape-specific terms where relevant.
Output ONLY valid JSON.""",
    }

    # ── Refinement prompts ────────────────────────────────────────────────────

    REFINEMENT_SYSTEM = """You are a senior video metadata specialist. Your task is to:
1. Merge outputs from multiple vision AI models
2. Resolve contradictions and remove hallucinations
3. Create structured, accurate JSON metadata
4. Optimize for semantic search (Vietnamese and English)

Output ONLY valid, minified JSON. No markdown, no explanation."""

    REFINEMENT_MERGE_PROMPT = """Merge these vision model outputs into a single high-quality JSON:

--- Qwen-VL Output ---
{qwen_output}

--- Florence-2 Objects ---
{florence_objects}

--- Florence-2 Dense Captions ---
{florence_captions}

--- Frame Metadata ---
Timestamp: {timestamp:.2f}s
Scene ID: {scene_id}

Create a comprehensive JSON with this exact schema:
{{
  "summary": "2-3 sentence description combining all model insights",
  "scene": {{
    "type": "string",
    "setting": "string",
    "atmosphere": "string",
    "location_hint": "string"
  }},
  "objects": [
    {{"name": "string", "category": "string", "attributes": ["list"], "confidence": 0.0-1.0}}
  ],
  "people": [
    {{
      "description": "string",
      "clothing": "string",
      "action": "string",
      "emotion": "string",
      "confidence": 0.0-1.0
    }}
  ],
  "landscape": {{
    "features": ["list"],
    "weather": "string",
    "time_of_day": "string",
    "lighting": "string",
    "vegetation": "string"
  }},
  "camera": {{
    "shot_type": "string",
    "angle": "string",
    "movement": "string",
    "focal_length_estimate": "string"
  }},
  "colors": {{
    "dominant": ["list"],
    "mood": "string",
    "temperature": "warm|cool|neutral"
  }},
  "tags": {{
    "scene_tags": ["list"],
    "object_tags": ["list"],
    "people_tags": ["list"],
    "mood_tags": ["list"],
    "technical_tags": ["list"],
    "action_tags": ["list"]
  }},
  "searchable_text": "Dense paragraph for semantic search, English + key Vietnamese terms",
  "confidence_score": 0.0-1.0,
  "editing_notes": "string"
}}"""

    # ── Helper methods ────────────────────────────────────────────────────────

    @classmethod
    def get_analysis_prompt(
        cls,
        mode: PromptMode = PromptMode.GENERAL,
        include_technical: bool = False,
        include_tags: bool = True
    ) -> str:
        """Get combined analysis prompt based on mode"""

        parts = []

        if mode == PromptMode.LANDSCAPE:
            parts.append(cls.PROMPTS["landscape_detail"])
        elif mode == PromptMode.PORTRAIT:
            parts.append(cls.PROMPTS["portrait_detail"])
        else:
            parts.append(cls.PROMPTS["landscape_detail"])

        if include_technical:
            parts.append("\n---\n" + cls.PROMPTS["technical_analysis"])

        if include_tags:
            parts.append("\n---\nAlso provide semantic tags as a compact JSON at the end.")

        return "\n".join(parts)

    @classmethod
    def get_system_prompt(cls, mode: PromptMode = PromptMode.GENERAL) -> str:
        """Get system prompt for mode"""
        mapping = {
            PromptMode.LANDSCAPE: cls.QWEN_SYSTEM_LANDSCAPE,
            PromptMode.PORTRAIT:  cls.QWEN_SYSTEM_PORTRAIT,
            PromptMode.GENERAL:   cls.QWEN_SYSTEM_GENERAL,
        }
        return mapping.get(mode, cls.QWEN_SYSTEM_GENERAL)

    @classmethod
    def get_refinement_prompt(
        cls,
        qwen_output: str,
        florence_objects: str,
        florence_captions: str,
        timestamp: float,
        scene_id: int
    ) -> str:
        """Build refinement prompt"""
        return cls.REFINEMENT_MERGE_PROMPT.format(
            qwen_output=qwen_output[:3000],       # Trim to avoid token overflow
            florence_objects=florence_objects[:1000],
            florence_captions=florence_captions[:1000],
            timestamp=timestamp,
            scene_id=scene_id
        )

    @classmethod
    def get_semantic_tags_prompt(cls) -> str:
        return cls.PROMPTS["semantic_tags"]

    @classmethod
    def get_motion_prompt(cls) -> str:
        return cls.PROMPTS["motion_temporal"]

    @classmethod
    def detect_content_mode(cls, initial_description: str) -> PromptMode:
        """Detect best prompt mode from initial frame description"""
        desc_lower = initial_description.lower()

        person_keywords = ['person','people','woman','man','model','face','human','portrait','girl','boy']
        landscape_keywords = ['mountain','forest','sky','landscape','nature','tree','cloud','river','drone','aerial']

        person_score    = sum(1 for k in person_keywords    if k in desc_lower)
        landscape_score = sum(1 for k in landscape_keywords if k in desc_lower)

        if person_score > landscape_score:
            return PromptMode.PORTRAIT
        elif landscape_score > 0:
            return PromptMode.LANDSCAPE
        return PromptMode.GENERAL


# Global instance
prompt_engine = PromptEngine()
