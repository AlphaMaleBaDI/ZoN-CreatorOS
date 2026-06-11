import sys
import os
from youtube_transcript_api import YouTubeTranscriptApi

video_ids = ["2-taQsk5-OM", "liR2Pn5Zp9g", "_PORHv_-atI"]

for vid in video_ids:
    print(f"Fetching transcript for {vid}...")
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(vid)
        raw_data = transcript.to_raw_data()
        text = " ".join([t['text'] for t in raw_data])
        out_path = f"workspace/transcript_{vid}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved transcript for {vid} to {out_path} ({len(text)} chars)")
    except Exception as e:
        print(f"Error fetching {vid}: {e}")
