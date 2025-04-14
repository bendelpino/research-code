# Research Scraping & Summarizing Tools

This repository is a research-oriented collection of code designed primarily for scraping data and summarizing content. It includes projects that aim to facilitate research tasks by extracting and processing information from online sources.

## Repository Structure

- **BrowserUse**  Contains code that uses the BrowserUse agent to search the web.*Note: This project is still a work in progress.*
- **YouTube** Contains a script that integrates with Gemini to perform the following tasks:

  - Retrieve the first 20 YouTube videos that appear for a given keyword search.
  - Extract their transcripts.
  - Summarize the video content.

## Getting Started

### Prerequisites

Make sure you have the following:

- Python 3.x
- Gemini API key
- Youtube API key
- BrowserUse library --> https://github.com/browser-use/browser-use

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/your-repository.git
   cd your-repository
   ```

### Try them

yt_worflow.py 

- Run the code and the terminal will ask you to input a search term.

specific_yt_transcripts.py

- Run the code from a terminal with the URL to the video after the script name.
- 'python specific_yt_transcripts.py {*url}*
