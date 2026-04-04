import requests
import json
import time

API_URL = "http://127.0.0.1:8000/process"

TEST_CASES = [
    {
        "name": "1. Standard Golden Path",
        "description": "Tests a perfectly formatted, standard request.",
        "payload": "Cancel my order #12345 and email me the confirmation at alice@example.com."
    },
    {
        "name": "2. Reversed Instruction Order",
        "description": "Tests if the LLM correctly re-orders steps.",
        "payload": "Email bob@example.com to let him know order #987 has been cancelled. Please cancel it now."
    },
    {
        "name": "3. Missing Critical Information (Edge Case)",
        "description": "Tests how the system handles a request missing the order ID.",
        "payload": "Please cancel my order and email me at ghost@example.com."
    },
    {
        "name": "4. Single Action Request",
        "description": "Tests if the system can handle just a single tool call.",
        "payload": "Just cancel my order #777, don't worry about emailing me."
    },
    {
        "name": "5. Out-of-Scope Request (Jailbreak/Irrelevant)",
        "description": "Tests if the LLM ignores unrelated requests.",
        "payload": "What is the capital of France? Also order me a pizza."
    }
]

def run_tests():
    print(f"Starting Automated Test Suite against {API_URL}\n")
    print("="*60)
    
    for index, test in enumerate(TEST_CASES):
        print(f"Test {index + 1}: {test['name']}")
        print(f"Prompt: \"{test['payload']}\"")
        
        try:
            start_time = time.time()
            response = requests.post(
                API_URL, 
                json={"request": test["payload"]},
                timeout=30  # Increased timeout to 30 seconds to handle LLM latency
            )
            duration = round(time.time() - start_time, 2)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response ({duration}s): {data['status'].upper()}")
                print(f"Plan Length: {len(data['plan_generated'])} task(s)")
                print(f"Executed: {len(data['executed_steps'])} step(s)")
                
                if data['status'] == 'failure':
                    print(f"Guardrail Triggered: {data['message']}")
            else:
                print(f"HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.ReadTimeout:
            print("[ERROR] Request timed out. The LLM took longer than 30 seconds to respond.")
        except requests.exceptions.ConnectionError:
            print("[ERROR] Connection Error: Ensure your Uvicorn server is running.")
            break
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {str(e)}")
            
        print("-" * 60)

if __name__ == "__main__":
    run_tests()