import os
from typing import List, Dict
from datetime import datetime
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
import re

# Load environment variables
load_dotenv()

# Configure API keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not YOUTUBE_API_KEY:
    raise ValueError("Please set the YOUTUBE_API_KEY environment variable")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

# Initialize clients
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def get_youtube_videos(search_term: str, max_results: int = 20) -> List[Dict[str, str]]:
    """Fetch YouTube videos based on search term."""
    search_response = (
        youtube.search()
        .list(
            q=search_term,
            part="id,snippet",
            maxResults=max_results,
            type="video",
        )
        .execute()
    )

    video_ids = [item["id"]["videoId"] for item in search_response["items"]]
    videos_response = (
        youtube.videos()
        .list(part="snippet,statistics", id=",".join(video_ids))
        .execute()
    )

    videos = []
    for video in videos_response["items"]:
        video_info = {
            "title": video["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={video['id']}",
            "view_count": int(video["statistics"]["viewCount"]),
        }
        videos.append(video_info)

    return videos

def save_videos_to_file(videos: List[Dict[str, str]], search_term: str) -> str:
    """Save video results to a text file."""
    filename = f"results/{search_term}_videos.txt"
    os.makedirs("results", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"YouTube Search Results for: '{search_term}'\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for i, video in enumerate(videos, 1):
            f.write(f"Video #{i}\n")
            f.write(f"Title: {video['title']}\n")
            f.write(f"URL: {video['url']}\n")
            f.write(f"View Count: {video['view_count']:,}\n")
            f.write("-" * 80 + "\n\n")

    return filename

def get_video_id_from_url(url: str) -> str:
    """Extract video ID from YouTube URL."""
    patterns = [r"(?:v=|/)([0-9A-Za-z_-]{11}).*", r"youtu.be/([0-9A-Za-z_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_url: str) -> str:
    """Get transcript for a single YouTube video."""
    video_id = get_video_id_from_url(video_url)
    if not video_id:
        return "Could not extract video ID from URL"

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        formatter = TextFormatter()
        return formatter.format_transcript(transcript)
    except Exception as e:
        return f"Could not fetch transcript: {str(e)}"

def save_transcripts_to_file(videos: List[Dict[str, str]], search_term: str) -> str:
    """Save transcripts for all videos to a single file."""
    filename = f"results/{search_term}_transcripts.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"YouTube Video Transcripts for Search Term: '{search_term}'\n")
        f.write("=" * 80 + "\n\n")

        for i, video in enumerate(videos, 1):
            f.write(f"Video #{i}\n")
            f.write(f"Title: {video['title']}\n")
            f.write(f"URL: {video['url']}\n")
            f.write("-" * 80 + "\n\n")

            transcript = get_transcript(video["url"])
            f.write("TRANSCRIPT:\n")
            f.write(transcript)
            f.write("\n" + "=" * 80 + "\n\n")

    return filename

def generate_content(prompt: str) -> str:
    """Generate content using Gemini API with streaming."""
    model = "gemini-2.0-pro-exp-02-05"
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192,
        response_mime_type="text/plain",
    )

    response_text = ""
    for chunk in gemini_client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        response_text += chunk.text

    return response_text

def read_transcripts_file(search_term: str) -> List[Dict[str, str]]:
    """Read transcripts from the previously generated file."""
    filename = f"results/{search_term}_transcripts.txt"
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Could not find {filename}")

    videos = []
    current_video = {}
    current_transcript = []
    reading_transcript = False

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("Video #"):
            if current_video and current_transcript:
                current_video["transcript"] = "\n".join(current_transcript)
                videos.append(current_video.copy())
            current_video = {}
            current_transcript = []
            reading_transcript = False
        elif line.startswith("Title: "):
            current_video["title"] = line[7:]
        elif line.startswith("URL: "):
            current_video["url"] = line[5:]
        elif line == "TRANSCRIPT:":
            reading_transcript = True
        elif reading_transcript and line and not line.startswith("="):
            current_transcript.append(line)

    if current_video and current_transcript:
        current_video["transcript"] = "\n".join(current_transcript)
        videos.append(current_video.copy())

    return videos

def analyze_transcript(video: Dict[str, str]) -> Dict[str, str]:
    """Use Gemini to analyze a video transcript and generate a summary with quotes."""
    prompt = f"""
    Analyze the following transcripts from YouTube videos and provide:
    1. A concise summary (1 paragraph) of the main points and key ideas of each video.
    2. 10 or more relevant and impactful quotes from the transcript about the ideas below. 
       Any time the script mentiones on eof the keywords below, please extract the exact quote and include it.
        Please search for quotes about these ideas:
        - Product Management
        - Culture
        - Hiring
        - AI
        - Teams
        - Success
        - User Feedback
        - Business Strategies
        - Learning from Mistakes
        - Storytelling
        - Procrastination
        - Market Dynamics
        - Product Development
        - Sales & Go-to-Market Tactics
        - Design
        - SaaS = Software Fragmentation
        - Leadership
    3. Include the URL of the video in the analysis
    
    Title: {video['title']}
    Transcript:
    {video['transcript']}
    
    Please format your response as follows:
    SUMMARY:
    [Your summary here]
    
    QUOTES:
    1. "[ quote]"
    2. "[ quote]"
    3. "[ quote]"
    4. "[ quote]"
    5. "[ quote]"
    6. "[ quote]"
    7. "[ quote]"
    8. "[ quote]"
    9. "[ quote]"
    10. "[ quote]"
    
    URL:
    [Video URL]
    """

    try:
        analysis = generate_content(prompt)
        return {"title": video["title"], "url": video["url"], "analysis": analysis}
    except Exception as e:
        return {
            "title": video["title"],
            "url": video["url"],
            "analysis": f"Error analyzing transcript: {str(e)}",
        }

def save_summaries_to_file(analyses: List[Dict[str, str]], search_term: str) -> str:
    """Save the analyses to a structured markdown file."""
    filename = f"results/{search_term}_summaries.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# YouTube Video Summaries for '{search_term}'\n\n")

        for i, analysis in enumerate(analyses, 1):
            f.write(f"## Video #{i}: [{analysis['title']}]({analysis['url']})\n\n")

            sections = analysis["analysis"].split("\n\n")

            for section in sections:
                if section.startswith("SUMMARY:"):
                    f.write("### Summary\n\n")
                    f.write(section.replace("SUMMARY:", "").strip())
                    f.write("\n\n")
                elif section.startswith("QUOTES:"):
                    f.write("### Key Quotes\n\n")
                    quotes = section.replace("QUOTES:", "").strip().split("\n")
                    for quote in quotes:
                        if quote.strip():
                            f.write(f"- {quote.strip()}\n")
                    f.write("\n")
                elif section.startswith("URL:"):
                    continue
                else:
                    f.write(section + "\n\n")

            f.write("---\n\n")

    return filename

def main():
    search_term = input("Enter the search term for YouTube videos: ")
    
    try:
        # Step 1: Scrape YouTube videos
        print("\nStep 1: Fetching YouTube videos...")
        videos = get_youtube_videos(search_term)
        videos_file = save_videos_to_file(videos, search_term)
        print(f"Videos saved to: {videos_file}")

        # Step 2: Get transcripts
        print("\nStep 2: Fetching video transcripts...")
        transcripts_file = save_transcripts_to_file(videos, search_term)
        print(f"Transcripts saved to: {transcripts_file}")

        # Step 3: Generate summaries
        print("\nStep 3: Generating summaries with Gemini...")
        videos_with_transcripts = read_transcripts_file(search_term)
        analyses = []
        
        for i, video in enumerate(videos_with_transcripts, 1):
            print(f"Analyzing video {i}/{len(videos_with_transcripts)}: {video['title']}")
            analysis = analyze_transcript(video)
            analyses.append(analysis)
            
            if i < len(videos_with_transcripts):
                print("Waiting 10 seconds before next analysis...")
                time.sleep(10)

        summaries_file = save_summaries_to_file(analyses, search_term)
        print(f"\nSummaries have been saved to: {summaries_file}")

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main() 