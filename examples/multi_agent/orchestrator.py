"""
Multi-Agent Example - Orchestrator

This module coordinates multiple specialized A2A agents to complete complex tasks.
"""

import os
import sys
import argparse
import time
from typing import Dict, Any, List

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from a2a.client import A2AClient


class AgentOrchestrator:
    """
    Orchestrator for coordinating multiple A2A agents.
    """
    
    def __init__(
        self,
        knowledge_endpoint: str = "http://localhost:8001",
        reasoning_endpoint: str = "http://localhost:8002",
        creative_endpoint: str = "http://localhost:8003"
    ):
        """
        Initialize the orchestrator.
        
        Args:
            knowledge_endpoint: Endpoint for the Knowledge Agent
            reasoning_endpoint: Endpoint for the Reasoning Agent
            creative_endpoint: Endpoint for the Creative Agent
        """
        self.knowledge_client = A2AClient(knowledge_endpoint)
        self.reasoning_client = A2AClient(reasoning_endpoint)
        self.creative_client = A2AClient(creative_endpoint)
        
        # Verify connections and discover capabilities
        print("Connecting to agents...")
        self._verify_connections()
    
    def _verify_connections(self):
        """Verify connections to all agents and print their capabilities."""
        try:
            knowledge_card = self.knowledge_client.discover_agent()
            print(f"✓ Connected to Knowledge Agent: {knowledge_card['name']}")
            print(f"  Skills: {', '.join(skill['name'] for skill in knowledge_card['skills'])}")
            
            reasoning_card = self.reasoning_client.discover_agent()
            print(f"✓ Connected to Reasoning Agent: {reasoning_card['name']}")
            print(f"  Skills: {', '.join(skill['name'] for skill in reasoning_card['skills'])}")
            
            creative_card = self.creative_client.discover_agent()
            print(f"✓ Connected to Creative Agent: {creative_card['name']}")
            print(f"  Skills: {', '.join(skill['name'] for skill in creative_card['skills'])}")
            
            print("\nAll agents connected successfully.\n")
        except Exception as e:
            print(f"Error connecting to agents: {e}")
            print("Please ensure all agent servers are running.")
            sys.exit(1)
    
    def _extract_content(self, response: Dict[str, Any]) -> str:
        """Extract text content from an agent response."""
        if "message" in response:
            for part in response["message"]["parts"]:
                if part["type"] == "text":
                    return part["content"]
        
        return str(response)  # Fallback
    
    def process_topic(self, topic: str) -> Dict[str, str]:
        """
        Process a topic using all three agents.
        
        Args:
            topic: The topic to process
            
        Returns:
            Dictionary with responses from each agent
        """
        print(f"Processing topic: '{topic}'")
        
        # Define prompts for each agent
        knowledge_prompt = f"Provide factual information and key statistics about {topic}. Include important data points, historical context, and current state."
        reasoning_prompt = f"Analyze the implications, challenges, and opportunities related to {topic}. Consider economic, social, and technological factors."
        creative_prompt = f"Create an engaging introduction that explains why {topic} is important and relevant today. Make it compelling for a general audience."
        
        # Send requests to all agents
        print("\n1. Gathering factual information from Knowledge Agent...")
        knowledge_response = self.knowledge_client.chat(knowledge_prompt)
        knowledge_content = self._extract_content(knowledge_response)
        
        print("2. Analyzing implications with Reasoning Agent...")
        reasoning_response = self.reasoning_client.chat(reasoning_prompt)
        reasoning_content = self._extract_content(reasoning_response)
        
        print("3. Creating engaging narrative with Creative Agent...")
        creative_response = self.creative_client.chat(creative_prompt)
        creative_content = self._extract_content(creative_response)
        
        # Return all responses
        return {
            "knowledge": knowledge_content,
            "reasoning": reasoning_content,
            "creative": creative_content
        }
    
    def generate_report(self, topic: str, responses: Dict[str, str]) -> str:
        """
        Generate a comprehensive report based on agent responses.
        
        Args:
            topic: The original topic
            responses: Responses from each agent
            
        Returns:
            Formatted report
        """
        # Send the combined insights to the creative agent for final coherent presentation
        synthesis_prompt = f"""
        Create a comprehensive, well-structured article about {topic} using the following three components:
        
        1. INTRODUCTION:
        {responses['creative']}
        
        2. FACTS AND CONTEXT:
        {responses['knowledge']}
        
        3. ANALYSIS AND IMPLICATIONS:
        {responses['reasoning']}
        
        Synthesize these into a cohesive, engaging article with appropriate sections and a conclusion.
        Make the transitions between sections smooth and natural.
        """
        
        print("\n4. Synthesizing final report...")
        synthesis_response = self.creative_client.chat(synthesis_prompt)
        synthesis_content = self._extract_content(synthesis_response)
        
        return f"# Comprehensive Analysis: {topic.title()}\n\n{synthesis_content}"


def main():
    """Run the multi-agent orchestration example."""
    parser = argparse.ArgumentParser(description="A2A Multi-Agent Orchestrator")
    parser.add_argument("--topic", type=str, required=True, help="The topic to analyze")
    parser.add_argument("--knowledge-endpoint", type=str, default="http://localhost:8001", help="Knowledge Agent endpoint")
    parser.add_argument("--reasoning-endpoint", type=str, default="http://localhost:8002", help="Reasoning Agent endpoint")
    parser.add_argument("--creative-endpoint", type=str, default="http://localhost:8003", help="Creative Agent endpoint")
    
    args = parser.parse_args()
    
    # Create the orchestrator
    orchestrator = AgentOrchestrator(
        knowledge_endpoint=args.knowledge_endpoint,
        reasoning_endpoint=args.reasoning_endpoint,
        creative_endpoint=args.creative_endpoint
    )
    
    # Process the topic
    responses = orchestrator.process_topic(args.topic)
    
    # Generate and print the final report
    report = orchestrator.generate_report(args.topic, responses)
    
    print("\n" + "="*80)
    print("\nFINAL REPORT:\n")
    print(report)
    print("\n" + "="*80)
    
    # Save the report to a file
    filename = f"{args.topic.replace(' ', '_').lower()}_report.md"
    with open(filename, "w") as f:
        f.write(report)
    
    print(f"\nReport saved to {filename}")


if __name__ == "__main__":
    main() 