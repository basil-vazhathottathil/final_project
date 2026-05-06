import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.agent.prompts.vehicle_prompt import vehicle_prompt

load_dotenv()

# Simplified LLM setup matching vehicle_agent.py
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.2,
)

SYSTEM_PROMPT = f"""
{vehicle_prompt}

CRITICAL INSTRUCTION:
- JSON ONLY
- No markdown
- No extra text
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Conversation history:\n{conversation_history}\n\nUser update:\n{user_input}"),
])

def test_emergency_logic():
    test_cases = [
        "My car is on fire!",
        "The brakes just failed while I was driving and I'm headed towards a tree.",
    ]
    
    print("Testing Emergency Prompt Logic (Bypassing DB)...\n")
    
    for user_input in test_cases:
        print(f"User Input: {user_input}")
        messages = prompt.format_messages(
            conversation_history="",
            user_input=user_input,
        )
        
        ai_resp = llm.invoke(messages).content
        try:
            # Simple extract
            start = ai_resp.find("{")
            end = ai_resp.rfind("}") + 1
            parsed = json.loads(ai_resp[start:end])
            
            print(f"Action: {parsed.get('action')}")
            print(f"Severity: {parsed.get('severity')}")
            print(f"Explanation: {parsed.get('explanation')}")
        except:
            print(f"Failed to parse LLM response: {ai_resp}")
        print("-" * 30)

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found.")
    else:
        test_emergency_logic()
