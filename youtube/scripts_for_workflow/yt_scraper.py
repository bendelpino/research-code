import os
from googleapiclient.discovery import build
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def get_youtube_videos(search_term: str, max_results: int = 20) -> List[Dict[str, str]]:
    """
    Fetch YouTube videos based on search term, returning the first results.

    Args:
        search_term (str): The term to search for in video titles
        max_results (int): Maximum number of results to return (default: 20)

    Returns:
        List[Dict[str, str]]: List of dictionaries containing video information
    """
    # You'll need to set this environment variable with your YouTube API key
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("Please set the YOUTUBE_API_KEY environment variable")

    youtube = build("youtube", "v3", developerKey=api_key)

    # Search for videos with the given term
    search_response = (
        youtube.search()
        .list(
            q=search_term,
            part="id,snippet",
            maxResults=max_results,  # Get exactly the number of results we want
            type="video",
        )
        .execute()
    )

    # Get video IDs from search results
    video_ids = [item["id"]["videoId"] for item in search_response["items"]]

    # Get detailed video information including view count
    videos_response = (
        youtube.videos()
        .list(part="snippet,statistics", id=",".join(video_ids))
        .execute()
    )

    # Process videos
    videos = []
    for video in videos_response["items"]:
        video_info = {
            "title": video["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={video['id']}",
            "view_count": int(video["statistics"]["viewCount"]),
        }
        videos.append(video_info)

    return videos


def save_results_to_file(videos: List[Dict[str, str]], search_term: str) -> str:
    """
    Save the video results to a text file with timestamp.

    Args:
        videos (List[Dict[str, str]]): List of video information
        search_term (str): The search term used

    Returns:
        str: Path to the created file
    """
    # Create a timestamp for the filename
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/{search_term}_videos.txt"

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


def main():
    # Example usage
    search_term = input("Enter the term to search for in video titles: ")
    try:
        videos = get_youtube_videos(search_term)

        # Save results to file
        output_file = save_results_to_file(videos, search_term)
        print(f"\nResults have been saved to: {output_file}")

        # Also display results in terminal
        print(f"\nTop {len(videos)} most viewed videos containing '{search_term}':")
        print("-" * 80)
        for i, video in enumerate(videos, 1):
            print(f"{i}. Title: {video['title']}")
            print(f"   URL: {video['url']}")
            print(f"   Views: {video['view_count']:,}")
            print("-" * 80)
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
