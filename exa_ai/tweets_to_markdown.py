from exa_py import Exa
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import json

load_dotenv()

exa = Exa(os.getenv("EXA_API_KEY"))


def clean_tweet_text(text):
    """Clean up tweet text to make it more readable in markdown"""
    if not text:
        return "No text available"

    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remove Twitter metadata that often appears in the text
    metadata_patterns = [
        r"\|\s*created_at:.*?(\||$)",
        r"\|\s*favorite_count:.*?(\||$)",
        r"\|\s*lang:.*?(\||$)",
        r"\|\s*profile_url:.*?(\||$)",
        r"\|\s*name:.*?(\||$)",
        r"\|\s*favourites_count:.*?(\||$)",
        r"\|\s*followers_count:.*?(\||$)",
        r"\|\s*friends_count:.*?(\||$)",
        r"\|\s*statuses_count:.*?(\||$)",
        r"\|\s*media_count:.*?(\||$)",
        r"created_at:.*?(\n|$)",
        r"favourites_count:.*?(\n|$)",
        r"friends_count:.*?(\n|$)",
        r"name:.*?(\n|$)",
    ]

    for pattern in metadata_patterns:
        text = re.sub(pattern, "", text)

    # Check if the text appears to be JSON
    if (text.strip().startswith("{") and "}" in text) or (
        text.strip().startswith('"{"') and '}"' in text
    ):
        try:
            # Try to extract just the JSON part
            json_match = re.search(r"({.*})", text)
            if json_match:
                json_str = json_match.group(1)
                # Parse and extract useful information
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        # Extract useful information
                        useful_info = []

                        # Try to get description or full_text from various nested locations
                        description = None
                        if "description" in parsed:
                            description = parsed["description"]
                        elif "legacy" in parsed and "description" in parsed["legacy"]:
                            description = parsed["legacy"]["description"]

                        full_text = None
                        if "full_text" in parsed:
                            full_text = parsed["full_text"]
                        elif "legacy" in parsed and "full_text" in parsed["legacy"]:
                            full_text = parsed["legacy"]["full_text"]

                        name = None
                        if "name" in parsed:
                            name = parsed["name"]
                        elif "legacy" in parsed and "name" in parsed["legacy"]:
                            name = parsed["legacy"]["name"]

                        # Add the extracted information to our useful_info list
                        if name:
                            useful_info.append(f"**Name:** {name}")
                        if description:
                            useful_info.append(f"**Bio:** {description}")
                        if full_text:
                            useful_info.append(f"**Tweet:** {full_text}")

                        # If we found useful information, return it
                        if useful_info:
                            return "\n\n".join(useful_info)
                except:
                    # If JSON parsing fails at this level, continue with regular cleaning
                    pass
        except:
            # If JSON parsing fails, continue with regular cleaning
            pass

    # Remove escaped characters and clean up whitespace
    text = text.replace("\\n", " ").replace("\\r", " ")
    text = re.sub(r"\s+", " ", text).strip()

    # If the text is still very long and looks like JSON (contains lots of special characters)
    if len(text) > 500 and re.search(r'[{}\[\]"\\]', text):
        return "Complex tweet data that couldn't be parsed cleanly. Please check the original tweet."

    return text


def extract_tweet_date(result):
    """Extract and format the tweet date"""
    if hasattr(result, "published_date") and result.published_date:
        try:
            # Try to parse the ISO date format
            date_obj = datetime.fromisoformat(
                result.published_date.replace("Z", "+00:00")
            )
            return date_obj.strftime("%B %d, %Y")
        except:
            return result.published_date
    return "Unknown date"


def save_tweets_to_markdown(results, output_file):
    """Save tweet results to a markdown file with headings for each result"""
    with open(output_file, "w", encoding="utf-8") as f:
        # Write the title and date
        current_date = datetime.now().strftime("%B %d, %Y")
        f.write(f"# AI Breakthrough Tweets\n\n")
        f.write(f"*Collected on {current_date}*\n\n")

        # Write each tweet as a section
        for i, result in enumerate(results, 1):
            # Extract tweet information
            url = result.url
            author = url.split("/")[3] if len(url.split("/")) > 3 else "Unknown"
            date = extract_tweet_date(result)
            text = clean_tweet_text(
                result.text if hasattr(result, "text") and result.text else ""
            )

            # Write the section
            f.write(f"## Tweet {i}: @{author}\n\n")
            f.write(f"**Date:** {date}\n\n")
            f.write(f"**URL:** [{url}]({url})\n\n")
            f.write(f"**Content:**\n\n{text}\n\n")
            f.write("---\n\n")

        f.write(f"*Total tweets collected: {len(results)}*")

    print(f"Successfully saved {len(results)} tweets to {output_file}")


if __name__ == "__main__":
    query = "here's an exciting breakthrough in artificial intelligence:"
    include_domains = ["twitter.com", "x.com"]
    num_results = 10

    # Calculate the date for five days ago
    five_days_ago = (datetime.now() - timedelta(days=5)).isoformat()

    # Execute the search
    print(f"Searching for tweets about AI breakthroughs...")
    search_response = exa.search_and_contents(
        query,
        include_domains=include_domains,
        num_results=num_results,
        text=True,
        start_published_date=five_days_ago,
    )

    results = search_response.results
    print(f"Found {len(results)} tweets")

    # Save to markdown file
    output_file = "ai_breakthrough_tweets.md"
    save_tweets_to_markdown(results, output_file)
