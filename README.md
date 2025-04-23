# Google's Agent2Agent (A2A) Protocol: Ollama Implementation

Medium Article:
https://medium.com/@CorticalFlow/googles-agent2agent-a2a-protocol-implementation-with-ollama-integration-27f1c9f2d4d3

This repository demonstrates an implementation of Google's Agent2Agent (A2A) protocol integrated with Ollama for local LLM inference. It now also includes integration with Model Context Protocol (MCP) for tool usage and sharing.

## Project Structure

```
lab-a2a-ollama-2/
├── a2a/                    # Core A2A implementation
│   ├── core/               # Core components
│   │   ├── agent_card.py   # A2A agent capability discovery
│   │   ├── task_manager.py # Task lifecycle management
│   │   ├── message_handler.py # Message exchange
│   │   ├── a2a_ollama.py   # Ollama integration
│   │   ├── a2a_mcp_bridge.py # Bridge between A2A and MCP
│   │   └── mcp/            # MCP integration
│   │       ├── mcp_client.py # Connect to external MCP servers
│   │       ├── mcp_server.py # Expose agent capabilities as MCP tools
│   │       ├── mcp_tool_manager.py # Register and manage MCP tools
│   │       └── mcp_schemas.py # MCP-specific data structures
│   ├── server.py           # A2A server implementation
│   └── client.py           # A2A client implementation
├── examples/               # Example implementations
│   ├── simple_chat/        # Basic agent chat example
│   ├── multi_agent/        # Multiple agents working together
│   ├── sse_streaming/      # Real-time streaming with Server-Sent Events
│   ├── webhook_notifications/ # Proactive task status updates via webhooks
│   └── mcp_integration/    # MCP integration examples
│       ├── agent_with_mcp_tools.py # Agent using external MCP tools
│       ├── agent_exposing_mcp.py # Agent exposing capabilities via MCP
│       └── multi_agent_mcp_bridge.py # Agents sharing tools via A2A+MCP
└── requirements.txt        # Project dependencies
```

## Installation

### Option 1: Standard Installation

1. Ensure you have Python 3.8+ and Ollama installed
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Option 2: Using Conda Environment

1. Ensure you have Anaconda or Miniconda installed
2. Create a new conda environment:

```bash
conda create -n a2a-ollama python=3.10
conda activate a2a-ollama
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Final Steps (both options)

Make sure Ollama is running and has the required model:

```bash
ollama pull gemma3:27b
```

## Usage

### Simple Chat Example

```bash
cd examples/simple_chat
python run_agent.py
# In another terminal window
python chat_with_agent.py --message "What is the capital of France?"
```

This example demonstrates basic A2A functionality:
1. First terminal starts an A2A agent server on default port 8000
2. Second terminal runs a client that connects to the agent and sends a message
3. The agent processes the message and returns a response

Try different questions to test the agent's capabilities. The agent uses the Ollama model specified for generating responses.

### Multi-Agent Example

```bash
cd examples/multi_agent
python orchestrator.py --topic "renewable energy"
```

This example shows multiple agents collaborating on a task:
1. An orchestrator agent that breaks down the topic into subtasks
2. Research agents that gather information on specific aspects
3. An editor agent that compiles the research into a cohesive report

The orchestrator coordinates the workflow by:
- Analyzing the topic and identifying key research areas
- Assigning subtasks to appropriate research agents
- Collecting results and sending them to the editor
- Delivering the final compiled report

You can try different topics by changing the --topic parameter.

### SSE Streaming Example

```bash
cd examples/sse_streaming
python sse_server.py --port 8000
# In another terminal window
python sse_client.py --endpoint http://localhost:8000 --query "Explain quantum computing" --visualize
```

This example demonstrates real-time streaming of agent responses using Server-Sent Events (SSE):
1. The server runs an A2A agent that streams responses as they're generated
2. The client connects to the SSE endpoint and displays responses in real-time
3. With --visualize flag, tokens appear progressively as they're received

Benefits:
- Immediate feedback to users as responses are generated
- Improved perceived performance and user experience
- Better for long responses where waiting for completion would be frustrating

### Webhook Notifications Example

```bash
cd examples/webhook_notifications
python webhook_server.py --a2a-port 8000 --webhook-port 8001
# In another terminal window
python webhook_client.py --a2a-endpoint http://localhost:8000 --webhook-base http://localhost:8001
```

This example shows how to implement proactive task status updates:
1. A webhook server listens for task events (started, progress, completed)
2. The A2A agent sends notifications at key points during task processing
3. The client registers for webhook callbacks and receives real-time updates

This approach is ideal for:
- Asynchronous operations where immediate responses aren't expected
- Long-running tasks that may take significant time to complete
- Systems requiring event-based notification rather than polling

### MCP Integration Examples

#### Agent Using External MCP Tools

This example demonstrates an A2A agent that connects to an external MCP server and uses its tools.

```bash
cd examples/mcp_integration
python agent_with_mcp_tools.py --model llama3.3:70b --mcp_server http://localhost:3000
```

In this example:
1. The agent connects to an existing MCP server running at the specified URL
2. It discovers available tools provided by the MCP server
3. The agent can then use these tools to enhance its capabilities

This demonstrates how agents can extend their functionality by leveraging external tools without having to implement them directly.

#### Agent Exposing Capabilities as MCP Tools

This example demonstrates an A2A agent that exposes its own capabilities as MCP tools.

```bash
cd examples/mcp_integration
python agent_exposing_mcp.py --model llama3.3:70b --port 8000 --mcp_port 3000
```

In this example:
1. An A2A agent with built-in capabilities starts on port 8000
2. An MCP server starts on port 3000
3. The agent's capabilities are registered as tools in the MCP server
4. Other systems can connect to the MCP server to discover and use these tools

This shows how an agent can share its specialized capabilities with other agents or systems through the MCP protocol.

#### Multi-Agent System with MCP Bridge

This example demonstrates a full multi-agent system where agents communicate using A2A and share tools via MCP.

```bash
cd examples/mcp_integration
python multi_agent_mcp_bridge.py --model llama3.3:70b
```

> **Note:** If you're having issues with the `llama3.3:70b` model, you can use any other available Ollama model such as `llama2` or `gemma3:27b`. Check available models with `ollama list`.

You can enable detailed logging to troubleshoot connection issues:

```bash
# Run with DEBUG level logging for detailed output
python multi_agent_mcp_bridge.py --model llama3.3:70b --log-level DEBUG

# Run with INFO level logging (default)
python multi_agent_mcp_bridge.py --model llama3.3:70b --log-level INFO
```

This demo creates:
1. An MCP server on port 3000 that hosts common tools (weather and calculator)
2. A "Tool Provider Agent" on port 8000 that exposes its capabilities via MCP
3. A "Tool Consumer Agent" on port 8001 that discovers and uses MCP tools

When the demo runs, it automatically:
- Starts all servers and establishes connections
- Registers example tools (get_weather, calculate)
- Shows the discovered agent skills
- Tests the system with example questions that utilize MCP tools

To interact with the system manually after it starts:
1. The system will run through automated test questions
2. Wait for it to complete or send your own queries to the consumer agent
3. Connect to http://localhost:8001 with a REST client or use curl:
   ```bash
   curl -X POST http://localhost:8001/tasks -H "Content-Type: application/json" -d '{"inputs": {"question": "What is the weather in Tokyo and then calculate 25 * 16?"}}'
   ```

Example questions to try:
- "What's the weather like in Paris?"
- "Calculate 42 * 18"
- "Can you tell me the weather in London and calculate the square root of 144?"

Press Ctrl+C to exit when finished.



**Advanced Troubleshooting:**
- If the Tool Consumer server still doesn't start:
  1. Check the latest version of the code from GitHub, which contains additional fixes
  2. Verify Python requests package is installed: `pip install requests`
  3. Try accessing the MCP server directly in your browser: http://localhost:3000/.well-known/mcp.json
  4. If that doesn't work, your MCP server might not be properly exposing its endpoints
  5. You can still test the basic A2A functionality by connecting directly to the Tool Provider agent:
     ```bash
     curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"inputs": {"question": "Tell me a joke"}}'
     ```

## About MCP Integration

The Model Context Protocol (MCP) integration allows:

1. **Tool Access**: A2A agents can access external tools via MCP servers
2. **Tool Exposure**: A2A agents can expose their capabilities as MCP tools
3. **Tool Sharing**: Multiple agents can share tools across the A2A-MCP bridge

This creates a powerful ecosystem where agents can discover and use each other's tools dynamically.

## License

MIT 