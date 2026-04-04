import os
import json
import asyncio
import random
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Logging Configuration ---
# This sets up a professional logger with timestamps and log levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MiniAgent")

# Load environment variables
load_dotenv()

# Initialize the new client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="Mini Agent Orchestrator")

# --- Models ---
class UserRequest(BaseModel):
    request: str

# --- 1. Tool Execution (Mock Async Functions) ---

async def cancel_order(order_id: str) -> bool:
    """Mock asynchronous tool to cancel an order."""
    logger.info(f"TOOL EXECUTION: Attempting to cancel order #{order_id}...")
    await asyncio.sleep(0.5) 
    
    if random.random() < 0.20:
        logger.error(f"TOOL FAILED: System error while cancelling order #{order_id}.")
        return False
    
    logger.info(f"TOOL SUCCESS: Order #{order_id} has been successfully cancelled.")
    return True

async def send_email(email: str, message: str) -> bool:
    """Simulates sending an email."""
    logger.info(f"TOOL EXECUTION: Preparing to send email to {email}...")
    await asyncio.sleep(1.0) 
    logger.info(f"TOOL SUCCESS: Email dispatched to {email}. Content: '{message}'")
    return True

# --- 2. The Planner ---

async def plan_workflow(user_request: str) -> list:
    """Uses an LLM to parse the natural language input into actionable steps."""
    logger.info(f"PLANNER: Analyzing user request: '{user_request}'")
    
    prompt_text = f"""
    You are an intelligent order processing agent. 
    Parse the following user request into a JSON array of actionable steps (a DAG/list of tasks).
    
    Available actions:
    1. "cancel_order": Requires "order_id" (string).
    2. "send_email": Requires "email" (string) and "message" (string).
    
    Rules:
    - If the user asks to cancel an order and send an email, ensure "cancel_order" is the FIRST step.
    - Extract the relevant variables (order ID, email address) directly from the user's text.
    - If a required variable (like order_id) is missing from the user's text, DO NOT invent one. Omit the action.
    - If the user asks for something completely unrelated, return an empty array [].
    - Output ONLY a valid JSON array.
    
    User Request: "{user_request}"
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        plan = json.loads(response.text)
        logger.info(f"PLANNER: Successfully generated {len(plan)} task(s).")
        logger.debug(f"Generated Plan JSON: {json.dumps(plan)}")
        return plan
    except Exception as e:
        logger.error(f"PLANNER ERROR: Failed to generate plan. Reason: {e}")
        raise ValueError("Failed to parse request into an actionable plan.")

# --- 3. The Orchestrator & API Endpoint ---

@app.post("/process")
async def process_request(payload: UserRequest):
    """Single API endpoint that receives a natural language user request."""
    logger.info("--- NEW WORKFLOW STARTED ---")
    
    try:
        plan = await plan_workflow(payload.request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not plan:
         logger.warning("ORCHESTRATOR: Plan is empty. No actionable steps found.")
         return {"status": "success", "message": "No actionable steps identified from the request.", "plan_generated": [], "executed_steps": []}

    executed_steps = []
    
    for task in plan:
        action = task.get("action")
        logger.info(f"ORCHESTRATOR: Evaluating task -> {action}")
        
        if action == "cancel_order":
            order_id = task.get("order_id")
            if not order_id:
                logger.warning("ORCHESTRATOR: Skipping cancel_order tool. Missing 'order_id'.")
                continue
                
            success = await cancel_order(order_id)
            
            if not success:
                logger.warning(f"ORCHESTRATOR: Guardrail triggered! Halting workflow due to cancel_order failure.")
                return {
                    "status": "failure",
                    "message": f"Order #{order_id} could not be cancelled due to a system error. Workflow aborted.",
                    "plan_generated": plan,
                    "executed_steps": executed_steps
                }
            
            executed_steps.append({"action": "cancel_order", "order_id": order_id, "status": "success"})
            
        elif action == "send_email":
            email = task.get("email")
            message = task.get("message", "Your request has been processed.")
            if not email:
                logger.warning("ORCHESTRATOR: Skipping send_email tool. Missing 'email'.")
                continue
                
            await send_email(email, message)
            executed_steps.append({"action": "send_email", "email": email, "status": "success"})

    logger.info("--- WORKFLOW COMPLETED SUCCESSFULLY ---")
    return {
        "status": "success",
        "message": "Workflow completed successfully.",
        "plan_generated": plan,
        "executed_steps": executed_steps
    }