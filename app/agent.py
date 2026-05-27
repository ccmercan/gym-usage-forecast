"""
Agentic loop — Gemini via Vertex AI with function calling (ReAct style).

Flow per question:
  1. User question → send to Gemini with tool specs
  2. Gemini REASONS: decides which tool to call (or answers directly)
  3. We EXECUTE the tool against PostgreSQL
  4. OBSERVE: send the tool result back to Gemini
  5. Gemini SYNTHESIZES a natural language answer
  6. Repeat steps 2-5 if Gemini needs more data (max 5 iterations)

Why this matters for the JD:
  - "multi-agent systems using frameworks like ReAct" → this IS the ReAct loop
  - "connecting agents to enterprise knowledge bases" → PostgreSQL is the knowledge base
  - "debugging agent logic and optimizing tool selection" → tool call logs printed below
  - "tracing conversation IDs across microservices" → each /ask call gets a trace_id
"""
import os
import json
import uuid
from sqlalchemy.orm import Session

from app.tools import get_current_usage, get_best_times, query_gym_data

GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

SYSTEM_PROMPT = (
    "You are an AI assistant for the Raider Power Zone gym forecasting system "
    "at Texas Tech University. "
    "You have access to real gym usage data stored in a PostgreSQL database. "
    "When answering questions about gym usage, crowd levels, or best workout times, "
    "always use the available tools to fetch real data before answering. "
    "Be concise, friendly, and specific — include percentages and times in your answers. "
    "All times are in Central Time (CST/CDT)."
)

# ── Tool specs (JSON Schema) that Gemini reads to decide what to call ──────────
TOOL_SPECS = [
    {
        "name": "get_current_usage",
        "description": (
            "Get the most recent live usage percentage for gym facilities. "
            "Use this when the user asks about current crowd levels, how busy the gym "
            "is right now, or live/current usage."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "facility": {
                    "type": "string",
                    "description": (
                        "Optional facility name to filter "
                        "(e.g. 'Raider Power Zone', 'Pool'). "
                        "Leave empty for all facilities."
                    ),
                }
            },
        },
    },
    {
        "name": "get_best_times",
        "description": (
            "Get the best (least crowded) time windows to work out based on "
            "historical data. Use this when the user asks for recommendations, "
            "best times, or when to go to the gym."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "workout_duration_minutes": {
                    "type": "integer",
                    "description": "Duration of the workout in minutes (default 60).",
                },
                "weekday": {
                    "type": "string",
                    "description": (
                        "Day of week to check (e.g. 'Monday'). Defaults to today."
                    ),
                },
            },
        },
    },
    {
        "name": "query_gym_data",
        "description": (
            "Query historical gym usage data filtered by facility, weekday, and/or "
            "hour range. Use this when the user asks about patterns, trends, "
            "specific days, or specific hours."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "facility": {
                    "type": "string",
                    "description": "Facility name filter (e.g. 'Raider Power Zone').",
                },
                "weekday": {
                    "type": "string",
                    "description": "Day of week (e.g. 'Monday', 'Saturday').",
                },
                "start_hour": {
                    "type": "integer",
                    "description": "Start hour 24h format (e.g. 8 = 8am, 17 = 5pm).",
                },
                "end_hour": {
                    "type": "integer",
                    "description": "End hour 24h format exclusive (e.g. 10 = up to 10am).",
                },
            },
        },
    },
]


def _execute_tool(name: str, args: dict, db: Session, trace_id: str) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    print(f"[AGENT:{trace_id}] → tool={name} args={args}")

    if name == "get_current_usage":
        result = get_current_usage(db, facility=args.get("facility"))
    elif name == "get_best_times":
        result = get_best_times(
            db,
            workout_duration_minutes=int(args.get("workout_duration_minutes", 60)),
            weekday=args.get("weekday"),
        )
    elif name == "query_gym_data":
        result = query_gym_data(
            db,
            facility=args.get("facility"),
            weekday=args.get("weekday"),
            start_hour=args.get("start_hour"),
            end_hour=args.get("end_hour"),
        )
    else:
        result = {"error": f"Unknown tool: {name}"}

    result_str = json.dumps(result)
    print(f"[AGENT:{trace_id}] ← tool={name} result_preview={result_str[:120]}")
    return result_str


def ask(question: str, db: Session) -> str:
    """
    Main agentic entry point.

    Sends the question to Gemini with tool definitions, handles the
    function-calling loop (ReAct), and returns a natural language answer.
    Each call gets a unique trace_id for debugging across microservices.
    """
    trace_id = str(uuid.uuid4())[:8]
    print(f"[AGENT:{trace_id}] question={question!r}")

    # ── Guard: check dependencies and config ──────────────────────────────────
    try:
        import vertexai
        from vertexai.generative_models import (
            GenerativeModel,
            Tool,
            FunctionDeclaration,
            Part,
        )
    except ImportError:
        return (
            "AI assistant unavailable: google-cloud-aiplatform is not installed. "
            "Run: pip install google-cloud-aiplatform"
        )

    if not GCP_PROJECT:
        return (
            "AI assistant not configured: set the GCP_PROJECT_ID environment variable. "
            "See the setup guide in infrastructure/GCP_SETUP.md"
        )

    try:
        # ── Initialise Vertex AI SDK ──────────────────────────────────────────
        vertexai.init(project=GCP_PROJECT, location=GCP_REGION)

        # Build Gemini Tool object from our spec list
        declarations = [
            FunctionDeclaration(
                name=spec["name"],
                description=spec["description"],
                parameters=spec["parameters"],
            )
            for spec in TOOL_SPECS
        ]
        tools = [Tool(function_declarations=declarations)]

        model = GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=tools,
        )

        chat = model.start_chat()
        response = chat.send_message(question)

        # ── ReAct loop ────────────────────────────────────────────────────────
        # Gemini returns either tool calls OR a final text answer.
        # We keep looping until we get a text answer (max 5 steps).
        for iteration in range(5):
            candidate = response.candidates[0]

            # Collect any function calls Gemini wants to make
            function_calls = [
                part.function_call
                for part in candidate.content.parts
                if hasattr(part, "function_call") and part.function_call and part.function_call.name
            ]

            if not function_calls:
                # No tool calls → Gemini has a final answer
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"[AGENT:{trace_id}] done after {iteration} tool call(s)")
                        return part.text
                return "I was unable to generate a response. Please try again."

            # Execute each tool Gemini requested and collect responses
            tool_response_parts = []
            for fc in function_calls:
                result_str = _execute_tool(fc.name, dict(fc.args), db, trace_id)
                tool_response_parts.append(
                    Part.from_function_response(
                        name=fc.name,
                        response={"result": json.loads(result_str)},
                    )
                )

            # Send tool results back → Gemini reasons again
            response = chat.send_message(tool_response_parts)

        return "I reached the maximum reasoning steps. Please try rephrasing your question."

    except Exception as exc:
        import traceback

        traceback.print_exc()
        return f"An error occurred while processing your question: {exc}"
