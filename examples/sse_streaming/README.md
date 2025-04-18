# SSE Streaming Example

This example demonstrates how to use Server-Sent Events (SSE) for real-time streaming of agent responses in the A2A protocol.

## What is SSE?

Server-Sent Events (SSE) is a server push technology enabling a client to receive automatic updates from a server via an HTTP connection. SSE is especially useful for applications requiring real-time data streams, such as:

- Live chat applications
- Real-time analytics dashboards
- AI agent streaming responses
- Progress updates for long-running tasks

## Benefits of SSE for A2A Protocol

1. **Real-time Feedback**: Users see responses as they're being generated, providing immediate feedback
2. **Improved Perceived Performance**: Even if the overall response time is the same, seeing incremental progress makes the interaction feel faster
3. **Long-running Tasks**: Ideal for tasks that may take a while to complete
4. **Reduced Timeouts**: Keeps connections alive with continuous data flow, avoiding timeout issues
5. **Lower Overhead**: Lighter than WebSockets for unidirectional streaming

## Components

This example consists of two main parts:

- **sse_server.py**: A simple A2A-compatible server with SSE streaming support
- **sse_client.py**: A client that demonstrates how to consume SSE streams

## How It Works

1. The A2A protocol's core implementation includes built-in support for SSE streaming through the `/tasks/<task_id>/messages/stream` endpoint
2. The server sends chunks of the response as they become available
3. The client consumes these chunks in real-time, providing immediate feedback to the user

## Running the Example

### Start the Server

```bash
python sse_server.py --port 8000
```

This starts an A2A server on port 8000 with SSE streaming capabilities.

### Run the Client

Basic streaming:
```bash
python sse_client.py --endpoint http://localhost:8000
```

With a custom query:
```bash
python sse_client.py --endpoint http://localhost:8000 --query "Explain quantum computing in simple terms, paragraph by paragraph."
```

With visualization (adds a typing effect to better demonstrate streaming):
```bash
python sse_client.py --endpoint http://localhost:8000 --visualize
```

## Implementation Details

### Server-Side

The server uses the core A2A implementation which already includes SSE support. When the client makes a request to the streaming endpoint, the server:

1. Accepts the connection and sets the appropriate headers for SSE
2. Sends chunks of the response as they become available from the LLM
3. Includes event types to indicate different stages (started, chunk, completed)

### Client-Side

The client uses the A2A client's streaming capabilities to:

1. Establish a connection to the streaming endpoint
2. Process SSE events as they arrive
3. Extract and display content chunks in real-time

## A2A Protocol Compatibility

This implementation follows the A2A protocol's recommendations for streaming:

1. Uses the standard HTTP + SSE pattern for streaming
2. Structures events with appropriate metadata
3. Provides status updates throughout the streaming process
4. Gracefully handles completion and error cases 