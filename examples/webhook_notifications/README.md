# Webhook Notifications Example

This example demonstrates how to use webhook notifications for task status updates in the A2A protocol, allowing agents to proactively inform clients about changes and progress.

## What are Webhooks?

Webhooks are user-defined HTTP callbacks that are triggered by specific events. Unlike regular API calls where the client pulls information from the server, webhooks push information to the client when events occur. They are particularly useful for:

- Asynchronous operations
- Long-running tasks
- Real-time notifications
- Integration between systems
- Event-driven architectures

## Benefits of Webhooks for A2A Protocol

1. **Proactive Communication**: Agents can notify clients about status changes without requiring polling
2. **Reduced Latency**: Updates are received immediately when they occur
3. **Decoupled Architecture**: Allows for more flexible, loosely coupled systems
4. **Lower Resource Usage**: Eliminates the need for continuous polling
5. **Event-Driven Integration**: Enables seamless integration with event-driven architectures

## Components

This example consists of two main components:

- **webhook_server.py**: Sets up both an A2A agent server with webhook support and a webhook receiver server
- **webhook_client.py**: A client that interacts with the A2A agent and monitors webhook notifications

## How It Works

1. The core A2A implementation includes webhook notification support through configurable webhook URLs
2. The server sends HTTP POST requests to the configured webhook URL when key events occur
3. A webhook receiver processes and logs these notifications
4. The client can monitor the webhook logs to track task progress in real-time

## Running the Example

### Start the Server

```bash
python webhook_server.py --a2a-port 8000 --webhook-port 8001
```

This starts:
- An A2A server on port 8000 with webhook notification support
- A webhook receiver server on port 8001 that logs notifications

### Run the Client

```bash
python webhook_client.py --a2a-endpoint http://localhost:8000 --webhook-base http://localhost:8001
```

With a custom query:
```bash
python webhook_client.py --a2a-endpoint http://localhost:8000 --webhook-base http://localhost:8001 --query "Process this request while sending status updates via webhooks."
```

## Webhook Events

The A2A protocol sends webhook notifications for key task lifecycle events:

1. **Task Creation**: When a new task is created
2. **Status Changes**: When a task status changes (e.g., from "submitted" to "working")
3. **Task Completion**: When a task is completed
4. **Task Failure**: When a task encounters an error

Each webhook notification includes:
- Task ID
- Status
- Timestamp
- Event-specific data

## Implementation Details

### Server-Side

The webhook integration requires two components:

1. **A2A Server**: Configured with a webhook URL, it sends notifications at key points in the task lifecycle
2. **Webhook Receiver**: A separate server that listens for and processes webhook notifications

The A2A server is configured with the `webhook_url` parameter, which enables it to send notifications to the specified URL. No additional code is needed in the agent implementation as webhook support is built into the core A2A implementation.

### Client-Side

The client interacts with both:

1. **A2A Server**: To create tasks and send messages
2. **Webhook Receiver**: To monitor notifications and track task progress

## A2A Protocol Compatibility

This implementation follows the A2A protocol's recommendations for push notifications:

1. Uses standard HTTP POST requests for webhook notifications
2. Includes all necessary metadata with each notification
3. Handles all key task lifecycle events
4. Maintains consistency in notification format 