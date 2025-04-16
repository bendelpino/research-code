# Research Scraping & Summarizing Tools

This repository is a research-oriented collection of code designed primarily for scraping data and summarizing content. It includes projects that aim to facilitate research tasks by extracting and processing information from online sources.

## Repository Structure

- **BrowserUse**: Contains code that uses the BrowserUse agent to search the web. *Note: This project is still a work in progress.*

- **YouTube**: Contains a script that integrates with Gemini to perform the following tasks:
  - Retrieve the first 20 YouTube videos that appear for a given keyword search.
  - Extract their transcripts.
  - Summarize the video content.

- **Exa AI**: Contains tools for searching the web and processing content using the Exa API:
  - `search.py`: A powerful search tool that queries the web for relevant sources on a given topic and saves results as formatted markdown files. It automatically excludes Wikipedia domains and provides various filtering options.
  - `tweets_to_markdown_final.py`: A specialized tool that searches for tweets about AI breakthroughs and formats them into a clean markdown document with proper headings and content organization.

## Getting Started

### Prerequisites

Make sure you have the following:

- Python 3.x
- Gemini API key (for YouTube and BrowserUse scripts)
- YouTube API key (for YouTube scripts)
- Exa API key (for Exa AI scripts)
- BrowserUse library --> https://github.com/browser-use/browser-use

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   cd your-repository
   ```

### Try them

#### YouTube Tools

**yt_workflow.py**
- Run the code and the terminal will ask you to input a search term.

**specific_yt_transcripts.py**
- Run the code from a terminal with the URL to the video after the script name.
- `python specific_yt_transcripts.py {url}`

#### Exa AI Tools

**search.py**
- Search the web for information on a specific topic:
  ```bash
  python search.py "Your search query here"
  ```
- Use additional options for more specific searches:
  ```bash
  python search.py "Your search query" --num-results 20 --include-domains example.com --start-date 2024-01-01
  ```
- Results are saved as markdown files in the `exa_ai/results/` directory.

**tweets_to_markdown_final.py**
- Collect tweets about AI breakthroughs and save them in a formatted markdown file:
  ```bash
  python tweets_to_markdown_final.py
  ```
