import os
from dotenv import load_dotenv
from app.agent.vehicle_agent import run_vehicle_agent

load_dotenv()

def test_emergency():
    test_cases = [
        "My car is on fire!",
        "Smoke is coming from the engine and it smells like burning rubber.",
        "The brakes just failed while I was driving.",
    ]
    
    print("Testing Emergency Situations...\n")
    
    for user_input in test_cases:
        print(f"User Input: {user_input}")
        response = run_vehicle_agent(
            user_input=user_input,
            chat_id="test-emergency-chat",
            user_id="test-user",
            vehicle_id="test-vehicle"
        )
        
        print(f"Action: {response.get('action')}")
        print(f"Severity: {response.get('severity')}")
        print(f"Confidence: {response.get('confidence')}")
        print(f"Explanation: {response.get('explanation')}")
        print("-" * 30)

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in environment or .env file.")
    else:
        test_emergency()
