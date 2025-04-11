from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import asyncio
from browser_use import Agent, Browser, BrowserConfig, Controller
from browser_use.browser.context import BrowserContext
from pydantic import BaseModel
from typing import List
load_dotenv()

class Post(BaseModel):
    caption: str
    url: str

class Posts(BaseModel):
    posts: List[Post]

controller = Controller(output_model=Posts)

# Configure the browser to connect to your Chrome instance
# browser = Browser(
#     config=BrowserConfig(
#         # Specify the path to your Chrome executable
#         chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
#     )
# )

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable")

# Initialize the client
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Gemini model configuration
llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', google_api_key=GEMINI_API_KEY)
# planner_llm = ChatOpenAI(model='o3-mini') # We could add a planner LLM, which means that we use a different model #
# to make the agent stop every, say, four steps and plan before going ahead with the next step or next task. #
# We would need to add this planner LLM argument to the agent within the main function. #


async def main():
    initial_actions = [
	    {'open_tab': {'url': 'https://docs.browser-use.com/'}},
    ]
    # sensitive_data = {'x_name': '', 'x_password': ''}
    agent = Agent(
        task="Get the whole documentation from BrowserUse and put it into a Markdown file format",
        llm=llm,
        # browser=browser,
        controller=controller,
        initial_actions=initial_actions,
        # sensitive_data=sensitive_data,
        # planner_llm=planner_llm
        # planner_interval=4
    )
    result = await agent.run()
    print(result.final_result())
    data = result.final_result()
    
    # Write the final results to a Markdown file
    with open("browser_use_docs.md", "w", encoding="utf-8") as md_file:
        md_file.write(data)
        
    parsed: Posts = Posts.model_validate_json(data)
    # await browser.close()

asyncio.run(main())