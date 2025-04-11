from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from typing import List, Dict
import re
import os


def read_videos_from_file(search_term: str) -> List[Dict[str, str]]:
    """
    Read video information from the previously generated file.

    Args:
        search_term (str): The search term used (to find the correct file)

    Returns:
        List[Dict[str, str]]: List of video information
    """
    filename = f"results/{search_term}_videos.txt"

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Could not find {filename}. Please run yt_scraper.py first."
        )

    videos = []
    current_video = {}

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("Title: "):
            current_video = {"title": line[7:]}
        elif line.startswith("URL: "):
            current_video["url"] = line[5:]
            videos.append(current_video.copy())

    return videos


def get_video_id_from_url(url: str) -> str:
    """Extract video ID from YouTube URL."""
    # Match both standard and shortened YouTube URLs
    patterns = [r"(?:v=|/)([0-9A-Za-z_-]{11}).*", r"youtu.be/([0-9A-Za-z_-]{11})"]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(video_url: str) -> str:
    """
    Get transcript for a single YouTube video.

    Args:
        video_url (str): URL of the YouTube video

    Returns:
        str: Formatted transcript text
    """
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
    """
    Save transcripts for all videos to a single file.

    Args:
        videos (List[Dict[str, str]]): List of video information
        search_term (str): The search term used

    Returns:
        str: Path to the created file
    """
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


def main():
    search_term = input("Enter the search term used in yt_scraper.py: ")
    try:
        # Read videos from the previously generated file
        videos = read_videos_from_file(search_term)

        # Save transcripts to file
        output_file = save_transcripts_to_file(videos, search_term)
        print(f"\nTranscripts have been saved to: {output_file}")

    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")


if __name__ == "__main__":
    main()
