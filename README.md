# Google's Agent2Agent (A2A) Protocol: Ollama Implementation

This repository demonstrates an implementation of Google's Agent2Agent (A2A) protocol integrated with Ollama for local LLM inference.

## Project Structure

```
lab-a2a-ollama-2/
├── a2a/                    # Core A2A implementation
│   ├── core/               # Core components
│   │   ├── agent_card.py   # A2A agent capability discovery
│   │   ├── task_manager.py # Task lifecycle management
│   │   ├── message_handler.py # Message exchange
│   │   └── a2a_ollama.py   # Ollama integration
│   ├── server.py           # A2A server implementation
│   └── client.py           # A2A client implementation
├── examples/               # Example implementations
│   ├── simple_chat/        # Basic agent chat example
│   └── multi_agent/        # Multiple agents working together
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

### Multi-Agent Example

```bash
cd examples/multi_agent
python orchestrator.py --topic "renewable energy"
```

## License

MIT 