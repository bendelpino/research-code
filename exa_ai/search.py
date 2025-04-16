#!/usr/bin/env python3
"""
Exa Search Tool - Search the web for relevant sources on a given topic

This script uses the Exa API to search for information on a specified topic
and saves the results in a well-formatted markdown file.
"""

### Example run: python search.py "Thrive Capital Valuation 2025" --num-results 3

import os
import sys
import argparse
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from exa_py import Exa

# Load environment variables
load_dotenv()


def get_api_key() -> str:
    """Get the Exa API key from environment variables."""
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise ValueError(
            "EXA_API_KEY environment variable not found. Please set it in your .env file."
        )
    return api_key


def format_result_as_markdown(results: List[Dict[str, Any]], query: str) -> str:
    """Format search results as markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    markdown = f"# Search Results: {query}\n\n"
    markdown += f"*Search performed on: {now}*\n\n"

    for i, result in enumerate(results, 1):
        # Extract the important fields
        title = result.get("title", "No Title")
        url = result.get("url", "No URL")
        published_date = result.get("published_date", "Unknown date")

        # Format the date if it's in ISO format
        if published_date and published_date != "Unknown date":
            try:
                date_obj = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
                published_date = date_obj.strftime("%B %d, %Y")
            except (ValueError, AttributeError):
                pass

        # Extract text content if available
        text = result.get("text", "")
        if text:
            # Limit text preview to a reasonable length
            text_preview = text[:500] + "..." if len(text) > 500 else text
        else:
            text_preview = "No text content available"

        # Add source information
        source = result.get("source", "Unknown source")

        # Format the result as a markdown section
        markdown += f"## {i}. {title}\n\n"
        markdown += f"**URL:** [{url}]({url})\n\n"
        markdown += f"**Date:** {published_date}\n\n"
        markdown += f"**Source:** {source}\n\n"
        markdown += f"**Preview:**\n\n{text_preview}\n\n"
        markdown += "---\n\n"

    markdown += f"*Total results: {len(results)}*"
    return markdown


def search_exa(
    query: str,
    num_results: int = 10,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    text: bool = True,
    use_autoprompt: bool = False,
) -> List[Dict[str, Any]]:
    """
    Search the web using Exa API.

    Args:
        query: The search query
        num_results: Number of results to return
        include_domains: List of domains to include in search
        exclude_domains: List of domains to exclude from search
        start_published_date: Start date for published content (ISO format)
        end_published_date: End date for published content (ISO format)
        text: Whether to include the text content
        use_autoprompt: Whether to use Exa's autoprompt feature

    Returns:
        List of search results
    """
    try:
        exa = Exa(get_api_key())

        # Build search parameters
        search_params = {"query": query, "num_results": num_results, "text": text}

        # Add optional parameters if provided
        if include_domains:
            search_params["include_domains"] = include_domains

        # Always exclude Wikipedia domains
        if exclude_domains:
            # Add Wikipedia to the existing exclude_domains list
            exclude_domains.append("en.wikipedia.org")
            search_params["exclude_domains"] = exclude_domains
        else:
            # If no exclude_domains provided, just exclude Wikipedia
            search_params["exclude_domains"] = ["en.wikipedia.org"]
        if start_published_date:
            search_params["start_published_date"] = start_published_date
        if end_published_date:
            search_params["end_published_date"] = end_published_date
        if use_autoprompt:
            search_params["use_autoprompt"] = True

        # Execute the search
        search_response = exa.search_and_contents(**search_params)

        # Convert results to a list of dictionaries
        results = [result.__dict__ for result in search_response.results]
        return results

    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        return []


def save_results(
    results: List[Dict[str, Any]], query: str, output_format: str = "markdown"
) -> str:
    """
    Save search results to a file.

    Args:
        results: List of search results
        query: The original search query
        output_format: Format to save results (markdown or json)

    Returns:
        Path to the saved file
    """
    # Always store output files in the results directory
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    # Create a filename-safe version of the query
    safe_query = "".join(c if c.isalnum() else "_" for c in query)
    safe_query = safe_query[:30]  # Limit length

    # Prepare filename with timestamp
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if output_format.lower() == "json":
        filename = f"{safe_query}_{now}.json"
        filepath = os.path.join(results_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    else:  # Default to markdown
        filename = f"{safe_query}_{now}.md"
        filepath = os.path.join(results_dir, filename)

        markdown_content = format_result_as_markdown(results, query)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    return filepath


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Search the web using Exa API and save results."
    )

    parser.add_argument("query", nargs="?", default=None, help="Search query")
    parser.add_argument(
        "--num-results", "-n", type=int, default=10, help="Number of results to return"
    )
    parser.add_argument(
        "--include-domains", "-i", nargs="+", help="Domains to include in search"
    )
    parser.add_argument(
        "--exclude-domains", "-e", nargs="+", help="Domains to exclude from search"
    )
    parser.add_argument(
        "--start-date", help="Start date for published content (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", help="End date for published content (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--autoprompt", action="store_true", help="Use Exa's autoprompt feature"
    )

    return parser.parse_args()


def main():
    """Main function to run the script."""
    args = parse_arguments()

    # If no query provided via command line, use a default or prompt the user
    query = args.query
    if not query:
        query = input("Enter your search query: ")

    print(f"Searching for: {query}")

    # Convert dates to ISO format if provided
    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").isoformat()
        except ValueError:
            print(
                f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD.",
                file=sys.stderr,
            )

    end_date = None
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").isoformat()
        except ValueError:
            print(
                f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD.",
                file=sys.stderr,
            )

    # Execute the search
    results = search_exa(
        query=query,
        num_results=args.num_results,
        include_domains=args.include_domains,
        exclude_domains=args.exclude_domains,
        start_published_date=start_date,
        end_published_date=end_date,
        use_autoprompt=args.autoprompt,
    )

    if not results:
        print("No results found or an error occurred during search.")
        return

    # Save the results
    filepath = save_results(results, query, args.format)
    print(f"Found {len(results)} results. Saved to: {filepath}")


if __name__ == "__main__":
    main()
