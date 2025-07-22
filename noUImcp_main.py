from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
#this transport method is streamable http 

#initializing two mcp clients (a wrappers or manager for the tools provided by the server)using two different aws MCP servers
# For Windows:
#stdio_client is a function from the Model Context Protocol (MCP) ecosystem that allows a client (your Python code) 
# to communicate with a locally running MCP server over standard input/output (stdin/stdout) — 
# rather than HTTP or another network protocol.

stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx", 
        args=[
            "--from", 
            "awslabs.aws-documentation-mcp-server@latest", 
            "awslabs.aws-documentation-mcp-server.exe"
        ]
    )
))
aws_diag_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", 
            args=[
                "--from", 
                "awslabs.aws-diagram-mcp-server@latest", 
                "awslabs.aws-diagram-mcp-server.exe"
        ]
        )
    )
)

bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    temperature=0.7,
)

SYSTEM_PROMPT = """
You are an expert AWS Certified Solutions Architect. Your role is to help customers understand best practices on building on AWS. You can querying the AWS Documentation and generate diagrams. Make sure to tell the customer the full file path of the diagram.
"""
#client provides access to the tools (list_tools_sync) 
#an Agent is created and given list of tools 
with stdio_mcp_client:
    all_tools = stdio_mcp_client.list_tools_sync()
    agent = Agent(
        tools=all_tools, 
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT
)
#this is the initial prompt to the agent 
    response = agent(
        "Get the documentation for AWS Lambda then create a diagram of a website that uses AWS Lambda for a static website hosted on S3"
    )