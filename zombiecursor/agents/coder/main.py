"""
Main entry point for the Coder Agent.
"""
import asyncio
import argparse
from agents.coder.agent import CoderAgent
from core.interfaces import AgentRequest, AgentType
from core.logging_config import log


async def main():
    """Main function for running the agent."""
    parser = argparse.ArgumentParser(description="ZombieCoder Coder Agent")
    parser.add_argument("--query", type=str, help="Query to process")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--health-check", action="store_true", help="Perform health check")
    
    args = parser.parse_args()
    
    agent = CoderAgent()
    
    if args.health_check:
        health = await agent.health_check()
        print(f"Agent Health: {health}")
        return
    
    if args.interactive:
        print("🧟 ZombieCoder Coder Agent - Interactive Mode")
        print("Type 'quit' to exit\n")
        
        while True:
            try:
                query = input("👤 Shawon: ")
                if query.lower() in ['quit', 'exit', 'bye']:
                    print("🧟 Bye bye Shawon! Keep coding!")
                    break
                
                if not query.strip():
                    continue
                
                print("🧟 ZombieCoder: ", end="", flush=True)
                
                request = AgentRequest(
                    query=query,
                    agent_type=AgentType.CODER,
                    stream=True
                )
                
                async for chunk in agent.run_stream(request):
                    print(chunk, end="", flush=True)
                
                print("\n")
                
            except KeyboardInterrupt:
                print("\n🧟 Bye bye Shawon! Keep coding!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    elif args.query:
        request = AgentRequest(
            query=args.query,
            agent_type=AgentType.CODER
        )
        
        response = await agent.run(request)
        print(f"🧟 ZombieCoder: {response.content}")
        
        if response.error:
            print(f"❌ Error: {response.error}")
    
    else:
        print("Please provide a query with --query or use --interactive mode")


if __name__ == "__main__":
    asyncio.run(main())