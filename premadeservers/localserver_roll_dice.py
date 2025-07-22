from mcp.server.fastmcp import FastMCP
import boto3
from dotenv import load_dotenv
import os
import random

#load fastmcp
mcp = FastMCP("Query KB")

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("MODEL_ID")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")
MODEL_ARN = os.getenv("MODEL_ARN")

bedrock_agent_client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

@mcp.tool()
def dice_rool(sides: int = 6) -> str:
    return f"You rolled a {random.randint(1,sides)}."

#only run this file if it is the main module
if __name__ == "__main__":
    mcp.run(transport="stdio")
