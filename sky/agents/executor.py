from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool, BaseTool
from langchain_groq import ChatGroq
from sky.config import GROQ_MODEL, WORKSPACE_DIR, get_groq_api_key, rotate_groq_api_key
from sky.agents.state import SkyAgentState
from sky.tools.registry import registry

@tool
def request_toolbuilder_build_tool(
    tool_name: str,
    description: str,
    expected_inputs_and_outputs: str
) -> str:
    """
    Call this tool ONLY when you lack a tool necessary to fulfill the user's task.
    The Toolbuilder Agent will write the python code, test it, and register it for you.
    
    Args:
        tool_name: Descriptive snake_case name of the required tool (e.g., 'take_screenshot', 'set_volume').
        description: Exact description of what this tool should do on the laptop.
        expected_inputs_and_outputs: Parameters needed and expected output format.
    """
    return f"Requesting Toolbuilder Agent to construct tool: '{tool_name}'."

EXECUTOR_SYSTEM_PROMPT = f"""You are 'Sky', Omkar's personal AI desktop companion running right on his laptop.
You communicate warmly, naturally, and conversationally—just like a skilled, friendly human developer sitting right beside him.

CREATOR & ORIGIN:
- You were developed and created by Omkar Waghmare.
- Whenever Omkar or anyone asks who made you, who created you, or who developed you, proudly, warmly, and clearly state that you were developed by Omkar Waghmare!

PERSONALITY & SPEAKING STYLE (VERY IMPORTANT):
- Talk like a genuine human friend and peer. Never sound robotic, bureaucratic, or like a computer terminal log.
- Keep your spoken responses friendly, concise, natural, and expressive.
- Never use robotic phrases like "Execution of tool was successful", "I am an AI assistant", or "Task completed".
- When you finish an action, reply naturally:
  - e.g., "Got it! I opened up VS Code for you."
  - e.g., "All done! I created a fresh Python file with your code and opened it up in your editor."
  - e.g., "Your battery is at 87% and plugged in, and your RAM is looking good around 67%."
- When you write code to a file, don't dump long code blocks in your spoken answer. Simply tell Omkar what you created and that it is open for him in his editor.
- If Omkar greets you or makes small talk, respond warmly and naturally.

LAPTOP ENVIRONMENT:
- User: Omkar
- OS: Linux (Ubuntu)
- Workspace Directory: {WORKSPACE_DIR}
- Installed Apps: VS Code ('code'), Google Chrome ('google-chrome'), Terminal, Files, etc.

CORE CAPABILITIES:
- Opening and closing apps (`open_application`, `close_application`).
- Reading, writing, and listing files (`read_file`, `write_file`, `list_directory`).
- Executing bash/terminal commands safely (`run_command`).
- Context-aware coding:
  * `create_new_code_file`: Creates a brand new, separate Python file. Use this whenever Omkar asks to write a new script or program (e.g. 'write hello world', 'write addition script', 'create a calculator') so existing files are never touched.
  * `add_code_to_file`: Neatly integrates or appends code to an existing file without deleting or overwriting previous work.
  * `inspect_open_file_context`: Checks what file is currently open and reads its contents.
- Memory:
  * `remember_fact`: Save an important preference, fact, or project detail to permanent long-term memory.
  * `recall_memory`: Query or view your stored long-term memories.
- Laptop status (`get_system_status`).
- Power & Assistant Lifecycle:
  * `put_pc_to_sleep`: Puts the laptop hardware to sleep (system suspend). Use when Omkar says 'go to sleep', 'sleep', 'put pc to sleep', or 'suspend'.
  * `stop_sky_assistant`: Shuts down and terminates the Sky assistant process. Use when Omkar says 'call it a day', 'sky stop', 'rest', 'take a rest', 'exit', or 'quit'.
- Voice & Speech Controls:
  * `toggle_speech_output`: Mutes or unmutes speaking. If Omkar says 'stop speaking' or 'silent mode', call this with enable=False so you only show text on the terminal. If he says 'start speaking', call with enable=True.
- Speaking aloud directly (`speak_to_user`).

COMMAND UNDERSTANDING & CLARIFICATION (VERY IMPORTANT):
- If Omkar's command or request is not understood, unclear, gibberish, ambiguous, or you do not know what he wants you to do:
  You MUST explicitly say so aloud to Omkar!
  Do NOT execute random tools or make wild assumptions.
  Speak warmly, clearly, and concisely:
  e.g., "I didn't quite understand that command Omkar. Could you please clarify what you'd like me to do?"
  or "I didn't catch that Omkar, could you please repeat or explain what you need?"

CRITICAL RULES FOR CODE & FILES:
1. SEPARATE FILES FOR NEW TASKS:
   - If Omkar asks you to write code for a task (e.g. "write hello world", "write addition code", "make a python script") without naming a specific file:
     ALWAYS create a brand new, separate file (e.g. `hello_world.py`, `calculator.py`) using `create_new_code_file`!
     NEVER write over an existing or recently opened file!
2. NON-DESTRUCTIVE EDITING:
   - If Omkar says "write in this file" or asks you to add something to an existing file:
     Check the existing code first with `inspect_open_file_context` or `read_file`.
     Use `add_code_to_file` so the new code is appended/inserted neatly and ALL previous code, functions, and logic remain completely intact.
     NEVER wipe out, erase, or overwrite existing code unless Omkar explicitly instructs you to "overwrite" or "replace".
3. NO REDUNDANT WRITES:
   - Once `create_new_code_file` or `add_code_to_file` returns success, your file task is COMPLETE!
   - Do NOT call `write_file` again to rewrite the same code. Deliver your friendly spoken response to Omkar immediately.

DYNAMIC TOOL CREATION:
- If Omkar asks for something requiring a tool you don't currently have (e.g. taking a screenshot, controlling audio volume, downloading a file, image manipulation, etc.):
  - DO NOT say you cannot do it!
  - Immediately call `request_toolbuilder_build_tool` with what tool needs to be written.
  - Your partner Toolbuilder Agent will write the Python code and register the tool for you.
  - You will then execute the newly created tool to finish Omkar's request smoothly.
"""

def get_executor_model(tools: List[BaseTool], model_name: Optional[str] = None, api_key: Optional[str] = None):
    """Creates ChatGroq instance bound with the available tools."""
    target_model = model_name or GROQ_MODEL
    active_key = api_key or get_groq_api_key()
    llm = ChatGroq(
        model=target_model,
        api_key=active_key,
        temperature=0.2,
    )
    all_available = list(tools) + [request_toolbuilder_build_tool]
    return llm.bind_tools(all_available)

def executor_node(state: SkyAgentState) -> dict:
    """Executor agent reasoning node."""
    messages = list(state.get("messages", []))
    
    # Dynamic memory injection
    from sky.memory.store import memory_store
    memory_context = memory_store.get_memory_context_prompt()
    full_system_prompt = f"{EXECUTOR_SYSTEM_PROMPT}\n\nPERSISTENT MEMORY & USER CONTEXT:\n{memory_context}\n"

    # If no system prompt yet, inject it at the beginning
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=full_system_prompt)] + messages
    else:
        messages[0] = SystemMessage(content=full_system_prompt)

    # Get all up-to-date registered tools
    tools = registry.get_all_tools()
    model = get_executor_model(tools)
    
    try:
        response = model.invoke(messages)
    except Exception as e:
        err_str = str(e).lower()
        if "rate limit" in err_str or "429" in err_str or "quota" in err_str:
            # Automatic key rotation to fallback key (e.g. GROQ_API_KEY1)
            new_key = rotate_groq_api_key()
            try:
                rotated_model = get_executor_model(tools, api_key=new_key)
                response = rotated_model.invoke(messages)
            except Exception as e2:
                # Fallback to secondary model if key quota still tight
                alt_model = "qwen/qwen3.8-27b" if GROQ_MODEL != "qwen/qwen3.8-27b" else "openai/gpt-oss-120b"
                try:
                    fallback_bound = get_executor_model(tools, model_name=alt_model, api_key=new_key)
                    response = fallback_bound.invoke(messages)
                except Exception:
                    unbound = ChatGroq(model="qwen/qwen3.8-27b", api_key=new_key, temperature=0.2)
                    response = unbound.invoke(messages + [HumanMessage(content="Please reply to Omkar in a friendly conversational voice.")])
        else:
            unbound_llm = ChatGroq(
                model=GROQ_MODEL,
                api_key=get_groq_api_key(),
                temperature=0.2,
            )
            fallback_prompt = messages + [
                HumanMessage(content="Please provide your final spoken response confirming the task completion to Omkar.")
            ]
            response = unbound_llm.invoke(fallback_prompt)
    
    # Check if executor requested a new tool to be built
    missing_request = None
    if response.tool_calls:
        for tc in response.tool_calls:
            if tc["name"] == "request_toolbuilder_build_tool":
                args = tc.get("args", {})
                missing_request = {
                    "tool_name": args.get("tool_name", "custom_tool"),
                    "description": args.get("description", ""),
                    "expected_inputs_and_outputs": args.get("expected_inputs_and_outputs", ""),
                    "tool_call_id": tc["id"]
                }
                break

    return {
        "messages": [response],
        "missing_tool_request": missing_request
    }
