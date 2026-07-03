from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from intelligence.nafasai_prompt import AGENT_PROMPT
from intelligence.tools.current_aqi import current_aqi
from intelligence.tools.forecast import forecast
from intelligence.tools.trend import trend
from intelligence.tools.health import health

import os
from dotenv import load_dotenv
load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY", "")
os.environ["GOOGLE_API_KEY"] = gemini_key
os.environ["GEMINI_API_KEY"] = gemini_key



nafasai_agent = Agent(
    name="NafasAI_Agent",
    model="gemini-3-flash-preview",
    instruction=AGENT_PROMPT,
    description="""
An intelligent air quality assistant that answers user queries by selecting and using the appropriate
tools to retrieve air quality information, forecasts, historical trends, and health recommendations.
""",
    tools=[
        current_aqi,
        forecast,
        trend,
        health,
    ],
)

# Session service
session_service = InMemorySessionService()

APP_NAME = "nafasai"

def ask_nafas(question: str, city: str = "karachi", profile: str = "general") -> str:
    """
    Run the NafasAI ADK agent and return its response as a string.
    """
    import asyncio

    async def _run():
        # Create a session
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id="web_user",
        )

        runner = Runner(
            agent=nafasai_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        # Build the message with city and profile context
        full_question = (
            f"The user is asking about {city.title()} unless they specify another city.\n"
            f"Health Profile: {profile}\n"
            f"Question: {question}"
        )

        message = types.Content(
            role="user",
            parts=[types.Part(text=full_question)]
        )

        final_response = ""
        async for event in runner.run_async(
            user_id="web_user",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break

        return final_response

    return asyncio.run(_run())