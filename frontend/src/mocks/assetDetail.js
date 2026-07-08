export const assetMock = {
  id: 'mock-id-123',
  title: "SWEDEN'S TRIP.mp4",
  mediaType: 'video',
  duration: 8, // seconds
  file_name: "sweden_trip_2024.mp4",
  file_path: "/uploads/sweden_trip_2024.mp4",
  file_size: "142 MB",
  resolution: "1920x1080",
  created_at: "2024-05-12T10:00:00Z",
  tags: [
    { name: "sweden", category: "location", source: "auto" },
    { name: "vlog", category: "content_type", source: "user_confirmed" },
    { name: "travel", category: "theme", source: "auto" },
    { name: "nature", category: "theme", source: "auto" }
  ],
  ai_caption: "A cinematic travel vlog showcasing the beautiful landscapes, cities, and nature of Sweden during summer. The video features drone shots of archipelagos, street views of Stockholm, and hiking in the northern mountains.",
};

export const sceneMock = [
  { id: 's1', start_sec: 0,   end_sec: 1.6,  thumbnail: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=320&q=70',  description: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains', subtitle: '"..bridge over a calm river.."' },
  { id: 's2', start_sec: 1.6,  end_sec: 3.2,  thumbnail: 'https://images.unsplash.com/photo-1520942702018-0862200e6873?w=320&q=70', description: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains', subtitle: '"..bridge over a calm river.."' },
  { id: 's3', start_sec: 3.2,  end_sec: 4.8,  thumbnail: 'https://images.unsplash.com/photo-1504893524553-b855bce32c67?w=320&q=70',  description: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains', subtitle: '"..bridge over a calm river.."' },
  { id: 's4', start_sec: 4.8,  end_sec: 6.4, thumbnail: 'https://images.unsplash.com/photo-1501854140801-50d01698950b?w=320&q=70', description: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains', subtitle: '"..bridge over a calm river.."' },
  { id: 's5', start_sec: 6.4, end_sec: 8.0, thumbnail: 'https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=320&q=70', description: 'Aerial view of stone bridge over a calm river surrounded by lush green mountains', subtitle: '"..bridge over a calm river.."' },
];

export const transcriptMock = [
  { start_sec: 0, end_sec: 0.8, text: "Welcome to our Sweden summer trip." },
  { start_sec: 0.8, end_sec: 1.7, text: "We started our journey in the beautiful archipelago." },
  { start_sec: 1.7, end_sec: 2.6, text: "Stockholm's old town is full of history." },
  { start_sec: 2.6, end_sec: 3.5, text: "The narrow streets are completely charming." },
  { start_sec: 3.5, end_sec: 4.4, text: "Next, we took a train heading north." },
  { start_sec: 4.4, end_sec: 5.3, text: "The views from the window were spectacular." },
  { start_sec: 5.3, end_sec: 6.2, text: "Finally, we reached the mountains." },
  { start_sec: 6.2, end_sec: 7.1, text: "Hiking here is a peaceful experience." },
  { start_sec: 7.1, end_sec: 8.0, text: "Thanks for watching our vlog." },
];

export const insightMock = {
  summary: "A beautiful aerial short of a stone brigde spanning a calm river, surounded by lush green moutains and trees. Soft daylight and scattered clouds create a peaceful and natural atmosphere.",
  moods: [
    { label: "CALM", score: 0.95 },
    { label: "RELAXING", score: 0.85 },
    { label: "NATURE", score: 0.98 },
    { label: "TRAVEL", score: 0.90 },
  ],
  objects: [
    { name: "BRIDGE", occurrences: [{ timestamp_start_sec: 0, timestamp_end_sec: 1.6, confidence: 0.95 }, { timestamp_start_sec: 3.2, timestamp_end_sec: 4.8, confidence: 0.88 }, { timestamp_start_sec: 6.4, timestamp_end_sec: 8.0, confidence: 0.92 }] },
    { name: "RIVER", occurrences: [{ timestamp_start_sec: 0, timestamp_end_sec: 3.2, confidence: 0.91 }, { timestamp_start_sec: 4.8, timestamp_end_sec: 8.0, confidence: 0.85 }] },
    { name: "MOUNTAINS", occurrences: [{ timestamp_start_sec: 0, timestamp_end_sec: 8.0, confidence: 0.98 }] },
    { name: "TREES", occurrences: [{ timestamp_start_sec: 1.6, timestamp_end_sec: 6.4, confidence: 0.89 }] },
    { name: "BOAT", occurrences: [{ timestamp_start_sec: 4.8, timestamp_end_sec: 5.5, confidence: 0.45 }] }
  ],
  best_for: [
    { name: "TRAVEL", category: "theme", source: "auto" },
    { name: "NATURAL FILM", category: "content_type", source: "auto" }
  ],
};
