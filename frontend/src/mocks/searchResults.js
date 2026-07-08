export const mockSearchResults = [
  {
    asset_id: "vid-001",
    asset_name: "Nature.mp4",
    media_type: "video",
    score: 0.94,
    tags: ["beach", "sunset"],
    video_duration: 300,
    ingested_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    scene: {
      scene_id: "scene-01",
      timestamp_start_sec: 142.5,
      thumbnail_url: "/thumbnails/vid-001.jpg",
      caption: "A beautiful sunset over the ocean with a generic scene description."
    }
  },
  {
    asset_id: "vid-002",
    asset_name: "Hiking_Trip.mp4",
    media_type: "video",
    score: 1.2,
    tags: ["mountain", "snow", "hiking"],
    video_duration: 45,
    ingested_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    scene: {
      scene_id: "scene-02",
      timestamp_start_sec: 65.0,
      thumbnail_url: null,
      caption: "A group of people hiking up a snowy mountain."
    }
  },
  {
    asset_id: "vid-004",
    asset_name: "City_Night_Walk.mp4",
    media_type: "video",
    score: 0.85,
    tags: ["city", "night", "neon"],
    video_duration: 120,
    ingested_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 15).toISOString(),
    scene: {
      scene_id: "scene-03",
      timestamp_start_sec: 10.0,
      thumbnail_url: null,
      caption: "A bustling city street at night, illuminated by neon signs."
    }
  },
  {
    asset_id: "vid-005",
    asset_name: "Ocean_Waves_Relax.mp4",
    media_type: "video",
    score: 0.72,
    tags: ["ocean", "nature"],
    video_duration: 600,
    ingested_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 40).toISOString(),
    scene: {
      scene_id: "scene-04",
      timestamp_start_sec: 12.0,
      thumbnail_url: null,
      caption: "Sound of waves crashing against the rocks."
    }
  },
  {
    asset_id: "vid-003",
    asset_name: "Cat_Sleeping.mp4",
    media_type: "video",
    score: 0.45,
    tags: ["cat", "indoor", "pet"],
    video_duration: 3650,
    ingested_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    scene: {
      scene_id: "scene-05",
      timestamp_start_sec: 3600.5,
      thumbnail_url: "/thumbnails/vid-003.jpg",
      caption: "A close-up shot of a cat sleeping on a sofa."
    }
  }
];
