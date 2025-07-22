from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from strands import Agent, tool
from strands.models import BedrockModel
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import os
import boto3
import logging


# Setup
logger = logging.getLogger(__name__)

app = FastAPI() #create REstapi server
templates = Jinja2Templates(directory="templates")
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("MODEL_ID")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")
MODEL_ARN = os.getenv("MODEL_ARN")

# AWS client
bedrock_agent_client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# ---------- Tool 2: Get Weather ----------
@tool
def get_weather_tool(location: str) -> str:
    try:
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {"q": f"{location}, USA", "format": "json", "limit": 1}
        geo_resp = requests.get(geo_url, params=geo_params, timeout=10, headers={"User-Agent": "weather-bot"})
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        if not geo_data:
            raise ValueError(f"City '{location}' not found.")
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "temperature_unit": "fahrenheit",
            "windspeed_unit": "mph"
        }
        weather_resp = requests.get(weather_url, params=weather_params, timeout=10)
        weather_resp.raise_for_status()
        current = weather_resp.json().get("current_weather", {})
        if not current:
            raise ValueError("Weather data unavailable.")
        summary = (
            f"Current weather in {location.title()}: "
            f"{current['temperature']}°F, "
            f"Wind {current['windspeed']} mph, "
            f"Condition code: {current['weathercode']}"
        )
        return {"location": location.title(), "weather": summary, "raw": current}
    except Exception as e:
        raise RuntimeError(f"Weather lookup error: {str(e)}")
@tool
def query_knowledge_base_tool(text: str) -> str:
    """
   Function for model invocation with knowledge base retrieval and generation.
    """
    if not KNOWLEDGE_BASE_ID or not MODEL_ARN:
        raise ValueError("Knowledge base configuration is missing.")
    
    try:
        response = bedrock_agent_client.retrieve_and_generate(
            input={"text": text},
            retrieveAndGenerateConfiguration={
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": MODEL_ARN
                },
                "type": "KNOWLEDGE_BASE"
            }
        )
        return {"response": response["output"]["text"]}
    except Exception as e:
        raise RuntimeError(f"Knowledge base error: {str(e)}")
# ---------- MCP Agent with Tools ----------
#action groups are used to group tools together
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-haiku-20240307-v1:0",
    temperature=0.7,
)
SYSTEM_PROMPT = """You are a friendly assistant that is responsible for getting the current weather, querying the knowledge base, 
and using the tools provided to you. If you don't have the answer from the tools provided to you, use your own knowledge."""

agent = Agent(
    tools=[get_weather_tool, query_knowledge_base_tool], 
    model=bedrock_model,
    system_prompt=SYSTEM_PROMPT
)

class QueryRequest(BaseModel):
    query: str

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index_draft.html", {"request": request})

@app.post("/ask")
def ask(request: QueryRequest):
    try:
        response = agent(request.query, stream=False)
        response_text = str(response)
        return {"response": response_text}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)