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
    model="moonshotai/kimi-k2-instruct-0905",
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

def test_internal_reasoning():
    test_cases = [
        "White smoke from exhaust, coolant disappearing, but no leaks visible",
        "Loud grinding noise from the front wheel when I press the brakes.",
    ]
    
    print("Testing Internal Reasoning (Chain of Thought)...\n")
    
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
            
            print(f"Internal Reasoning: {parsed.get('internal_reasoning')}")
            print(f"Diagnosis: {parsed.get('diagnosis')}")
            print(f"Action: {parsed.get('action')}")
        except:
            print(f"Failed to parse LLM response: {ai_resp}")
        print("-" * 30)

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found.")
    else:
        test_internal_reasoning()
