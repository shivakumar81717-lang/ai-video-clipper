import os
import subprocess
import json
from pydantic import BaseModel
import yt_dlp
from faster_whisper import WhisperModel
from google import genai
from google.genai import types

class HighlightClip(BaseModel):
    start_time: float
    end_time: float
    title: str
    reason: str

def download_video(url: str, output_path: str = "input.mp4") -> str:
    print(f"Downloading video from: {url}")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path,
        "overwrites": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

def transcribe_to_english(video_path: str):
    print("Loading Whisper model and transcribing audio to English...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_path, task="translate")
    
    transcript_list = []
    for seg in segments:
        transcript_list.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip()
        })
    return transcript_list

def find_best_part(transcript: list) -> HighlightClip:
    print("Analyzing transcript for the best highlight...")
    client = genai.Client()
    
    prompt = (
        "Analyze the following timestamped video transcript. "
        "Select the single most engaging, viral, or informative segment that lasts between 20 and 60 seconds. "
        "Return the exact start_time and end_time in seconds.\n\n"
        f"Transcript:\n{json.dumps(transcript)}"
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=HighlightClip,
        ),
    )
    return HighlightClip.model_validate_json(response.text)

def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def create_clip_srt(transcript: list, start: float, end: float, srt_path: str = "clip.srt"):
    print("Generating English SRT subtitles...")
    srt_lines = []
    counter = 1
    
    for seg in transcript:
        if seg["end"] > start and seg["start"] < end:
            adj_start = max(0.0, seg["start"] - start)
            adj_end = min(end - start, seg["end"] - start)
            
            srt_lines.append(f"{counter}")
            srt_lines.append(f"{format_srt_time(adj_start)} --> {format_srt_time(adj_end)}")
            srt_lines.append(f"{seg['text']}\n")
            counter += 1
            
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

def cut_and_burn_subtitles(input_video: str, srt_path: str, start: float, end: float, output_video: str = "final_clip.mp4"):
    print("Cutting video and burning subtitles with FFmpeg...")
    duration = end - start
    
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", input_video,
        "-t", str(duration),
        "-vf", f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2'",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_video
    ]
    subprocess.run(cmd, check=True)
    print(f"Done! Saved final video to {output_video}")

if __name__ == "__main__":
    video_url = input("Paste the video link: ").strip()
    raw_video = download_video(video_url)
    transcript = transcribe_to_english(raw_video)
    best_clip = find_best_part(transcript)
    
    print(f"\nSelected Clip: {best_clip.title}")
    print(f"Time: {best_clip.start_time}s to {best_clip.end_time}s")
    print(f"Reason: {best_clip.reason}\n")
    
    create_clip_srt(transcript, best_clip.start_time, best_clip.end_time)
    cut_and_burn_subtitles(raw_video, "clip.srt", best_clip.start_time, best_clip.end_time)
      
