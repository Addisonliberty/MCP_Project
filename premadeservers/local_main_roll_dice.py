from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

#initializing two mcp clients (a wrappers or manager for the tools provided by the server)using two different aws MCP servers
# For Windows:
#stdio_client is a function from the Model Context Protocol (MCP) ecosystem that allows a client (your Python code) 
# to communicate with a locally running MCP server over standard input/output (stdin/stdout) — 
# rather than HTTP or another network protocol.

#roll dice server using stdio transport
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uv",
        args=["run", "localserver_roll_dice.py"]
    )
))
aws_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-diagram-mcp-server"],
    )
))

#initialize model 
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    temperature=0.7,
)

SYSTEM_PROMPT = """
You are my personal assistant. Answer all my questions or use the tools provided to you.
"""
#client provides access to the tools (list_tools_sync) 
#an Agent is created and given list of tools 
with stdio_mcp_client, aws_mcp_client:
    #seeing what dools it can off us 
    all_tools = stdio_mcp_client.list_tools_sync() + aws_mcp_client.list_tools_sync()
    agent = Agent(
        tools=all_tools, 
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT
    )
    while True:
        user_input = input("\n🧑 You: ").strip()
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("👋 Goodbye!")
            break
        if not user_input:
            continue
        print(f"🤖 Agent: ")
        agent(user_input)
    #this is using standard IO 
    
#this is the initial prompt to the agent 
    # response = agent(
    #     "Get the documentation for AWS Lambda then create a diagram of a website that uses AWS Lambda for a static website hosted on S3"
    # )