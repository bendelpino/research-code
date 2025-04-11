import os
import base64
import time
from google import genai
from google.genai import types
from typing import List, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

# Initialize the client
client = genai.Client(api_key=GEMINI_API_KEY)


def generate_content(prompt: str) -> str:
    """
    Generate content using Gemini API with streaming.

    Args:
        prompt (str): The prompt to send to Gemini

    Returns:
        str: The complete generated response
    """
    model = "gemini-2.0-pro-exp-02-05"

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,  # Lower temperature for more focused responses
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192,
        response_mime_type="text/plain",
    )

    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        response_text += chunk.text

    return response_text


def read_transcripts_file(search_term: str) -> List[Dict[str, str]]:
    """
    Read transcripts from the previously generated file.

    Args:
        search_term (str): The search term used to find the file

    Returns:
        List[Dict[str, str]]: List of video information with transcripts
    """
    filename = f"results/{search_term}_transcripts.txt"

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Could not find {filename}. Please run yt_transcripts.py first."
        )

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

    # Add the last video
    if current_video and current_transcript:
        current_video["transcript"] = "\n".join(current_transcript)
        videos.append(current_video.copy())

    return videos


def analyze_transcript(video: Dict[str, str]) -> Dict[str, str]:
    """
    Use Gemini to analyze a video transcript and generate a summary with quotes.

    Args:
        video (Dict[str, str]): Video information including transcript

    Returns:
        Dict[str, str]: Analysis results including summary and quotes
    """
    prompt = f"""
    Analyze the following transcripts from YouTube videos and provide:
    1. A concise summary (1 paragraph) of the main points and key ideas of each video.
    2. 10 or more relevant and impactful quotes from the transcript about the ideas below. 
       Any time the script mentiones on eof the keywords below, please extract the exact quote and include it.
        Please search for quotes about these ideas:
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
    """
    Save the analyses to a structured markdown file.

    Args:
        analyses (List[Dict[str, str]]): List of video analyses
        search_term (str): The search term used

    Returns:
        str: Path to the created file
    """
    filename = f"results/{search_term}_summaries.md"

    with open(filename, "w", encoding="utf-8") as f:
        # Write header
        f.write(f"# YouTube Video Summaries for '{search_term}'\n\n")

        # Write each video analysis
        for i, analysis in enumerate(analyses, 1):
            # Video header with link
            f.write(f"## Video #{i}: [{analysis['title']}]({analysis['url']})\n\n")

            # Split the analysis into sections
            sections = analysis["analysis"].split("\n\n")

            # Process each section
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
                    # URL is already in the title link, so we can skip it
                    continue
                else:
                    f.write(section + "\n\n")

            f.write("---\n\n")  # Add a horizontal rule between videos

    return filename


def main():
    search_term = input("Enter the search term used in previous steps: ")
    try:
        # Read transcripts from file
        print("\nReading transcripts...")
        videos = read_transcripts_file(search_term)

        # Analyze each video
        print("\nAnalyzing transcripts with Gemini...")
        analyses = []
        for i, video in enumerate(videos, 1):
            print(f"Analyzing video {i}/{len(videos)}: {video['title']}")
            analysis = analyze_transcript(video)
            analyses.append(analysis)

            # Add delay between videos (except for the last one)
            if i < len(videos):
                print("Waiting 10 seconds before next analysis...")
                time.sleep(10) 

        # Save summaries to file
        output_file = save_summaries_to_file(analyses, search_term)
        print(f"\nSummaries have been saved to: {output_file}")

    except FileNotFoundError as e:
        print(f"\nError: {str(e)}")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")


if __name__ == "__main__":
    main()
