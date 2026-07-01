from google.adk.agents import Agent

from nafasai_prompt import AGENT_PROMPT

from intelligence.tools.current_aqi import current_aqi
from intelligence.tools.forecast import forecast
from intelligence.tools.trend import trend
from intelligence.tools.health import health


nafasai_agent = Agent(
    name="NafasAI_Agent",
    model="gemini-3.5-flash",
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