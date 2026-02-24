# test_random_issues.py

import asyncio
import random
from typing import Dict, List, Set
from app.obd.realistic_sim import RealisticOBDSimulator

async def test_simulator():
    print("🚀 Starting Randomized Issue Simulation Test...")
    simulator = RealisticOBDSimulator()
    
    triggered_issues = set()
    
    # Run for 200 steps to increase chance of seeing multiple issues
    # (Note: active_issue stays set once triggered in current impl, 
    # but we can run multiple sessions or modify simulator for multi-trigger)
    
    for i in range(1, 201):
        data = simulator.step()
        
        if simulator.active_issue:
            issue_name = simulator.active_issue["name"]
            if issue_name not in triggered_issues:
                print(f"✅ Step {i}: Triggered '{issue_name}'")
                print(f"   Data: {data}")
                triggered_issues.add(issue_name)
        
        if len(triggered_issues) >= 1: # Once one is triggered, it sticks
             break
             
        await asyncio.sleep(0.01) # fast simulation

    if not triggered_issues:
        print("❌ No issues triggered in 200 steps.")
    else:
        print(f"\n✨ Test passed! Triggered: {list(triggered_issues)}")

if __name__ == "__main__":
    asyncio.run(test_simulator())
