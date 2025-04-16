import google.generativeai as genai
import os
import argparse

# Load the API key from environment variable
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

# Set up the model
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config=generation_config,
)


def analyze_transcript(transcript_text):
    """
    Analyzes the transcript text using the Gemini API based on the provided prompt.

    Args:
        transcript_text (str): The content of the transcript.
        video_title (str): The title of the video (optional).

    Returns:
        str: The analysis result from the Gemini API, or None if an error occurs.
    """
    prompt_parts = [
        f"""Analyze the following transcripts from YouTube video and provide:
    1. A concise summary (1 paragraph) of the main points and key ideas.
    2. 10 or more relevant and impactful quotes from the transcript about the ideas below.
       Any time the script mentions one of the keywords below, please extract the exact quote and include it.
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

    Transcript:
    {transcript_text}

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
    11. [...]
    """
    ]

    try:
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a podcast transcript text file using Gemini API and save to Markdown."
    )
    parser.add_argument("transcript_file", help="Path to the transcript text file.")

    args = parser.parse_args()

    # Define the output directory
    output_dir = "/Users/benja/Desktop/research/research-code/youtube/results_from_single_files"
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Determine output filename
    base_name = os.path.basename(args.transcript_file)
    file_name_without_ext = os.path.splitext(base_name)[0]
    output_file_path = os.path.join(output_dir, f"{file_name_without_ext}.md")

    try:
        with open(args.transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read()
    except FileNotFoundError:
        print(f"Error: Transcript file not found at {args.transcript_file}")
        return
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        return

    print(f"Analyzing transcript from: {args.transcript_file}")
    print("-" * 30)

    analysis = analyze_transcript(transcript)

    if analysis:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f_out:
                f_out.write(analysis)
            print(f"\nAnalysis saved successfully to: {output_file_path}")
            print("-----------------------")
        except Exception as e:
            print(f"\nError writing analysis to file: {e}")
    else:
        print("Failed to get analysis from Gemini API.")


if __name__ == "__main__":
    main()
