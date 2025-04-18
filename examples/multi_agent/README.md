# Multi-Agent Collaboration with A2A

This example demonstrates how multiple specialized agents can collaborate using Google's A2A protocol to perform complex tasks.

## Architecture

The example includes three specialized agents and an orchestrator:

1. **Knowledge Agent** (port 8001): Provides factual information and research
2. **Reasoning Agent** (port 8002): Analyzes information and makes logical inferences
3. **Creative Agent** (port 8003): Generates creative content and text
4. **Orchestrator**: Coordinates the agents to complete a complex task

## How it Works

1. The orchestrator receives a topic from the user
2. The orchestrator delegates subtasks to each specialized agent:
   - Knowledge Agent: Research factual information about the topic
   - Reasoning Agent: Analyze implications, patterns, and connections
   - Creative Agent: Generate compelling narrative around the topic
3. The orchestrator synthesizes the responses to create a complete solution

## Running the Example

1. Make sure Ollama is running with the required models:
   ```
   ollama pull gemma3:27b
   ```

2. Start each agent in a separate terminal:
   ```
   # Terminal 1
   python agent_knowledge.py
   
   # Terminal 2
   python agent_reasoning.py
   
   # Terminal 3
   python agent_creative.py
   ```

3. Run the orchestrator with a topic:
   ```
   python orchestrator.py --topic "renewable energy"
   ```

## Example Workflow

1. User provides topic: "renewable energy"
2. Orchestrator breaks down the task:
   - Knowledge Agent: Research facts about renewable energy sources, adoption rates, etc.
   - Reasoning Agent: Analyze economic impact, policy implications, future trends
   - Creative Agent: Generate an engaging narrative explaining why renewable energy matters
3. Orchestrator combines the responses into a comprehensive analysis 