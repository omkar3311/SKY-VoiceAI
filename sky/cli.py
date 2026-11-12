import sys
import os
import random
import argparse
import threading
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from sky.config import GROQ_API_KEY, GROQ_MODEL, WORKSPACE_DIR, validate_environment
from sky.tools.registry import registry
from sky.agents.graph import sky_graph
from sky.voice.speaker import speaker

console = Console()

STARTUP_GREETINGS = [
    "Hello Omkar, nice to have you back again! I'm ready whenever you need me.",
    "Hi Omkar, I'm at your service. What are we building today?",
    "Hey Omkar, good to see you! Sky is online and listening.",
    "Welcome back Omkar! Everything's up and running, just say the word.",
    "Hi Omkar, hope you're having a great day. I'm right here if you need anything.",
    "Hey Omkar, nice to see you again! All systems are ready to go."
]

NO_INTERNET_PANEL = (
    "[bold red]⚠️  No Internet Connection[/bold red]\n\n"
    "[bold yellow]Ugh... Omkar, I don't have an internet connection right now![/bold yellow]\n\n"
    "[dim]I really cannot think or do anything without Wi-Fi or network access.\n"
    "Please connect me to the internet so I can help you![/dim]"
)

RECONNECTED_PANEL = (
    "[bold green]⚡ Internet Connected![/bold green]\n\n"
    "[bold green]Yahoo! Internet is back! Now I'm feeling the power in my veins![/bold green]\n\n"
    "[white]All AI models, brain tools, and voice systems are online.[/white]\n"
    "[dim]Ready for your commands, Omkar![/dim]"
)

def display_no_internet_warning():
    """Displays hardcoded upset offline warning panel."""
    console.print(Panel(
        NO_INTERNET_PANEL,
        title="[bold red]Offline Mode[/bold red]",
        border_style="red"
    ))

def display_reconnected_panel():
    """Displays enthusiastic green reconnection panel."""
    console.print(Panel(
        RECONNECTED_PANEL,
        title="[bold green]Back Online[/bold green]",
        border_style="green"
    ))

def start_network_monitor(execution_lock: threading.Lock, initial_online: bool, interval_seconds: float = 3.0):
    """
    Background daemon thread that monitors internet status.
    If Sky started offline and internet reconnects, Sky enthusiastically announces
    reconnection ('Yahoo! Now I'm feeling the power in my veins!').
    If internet drops while running, Sky warns Omkar.
    """
    import time
    def monitor_loop():
        was_online = initial_online
        while True:
            time.sleep(interval_seconds)
            from sky.config import is_internet_available
            is_online = is_internet_available()

            if not was_online and is_online:
                # Transition: Offline -> Online!
                was_online = True
                with execution_lock:
                    speaker.speak_reconnected(
                        on_start=display_reconnected_panel,
                        blocking=True
                    )
            elif was_online and not is_online:
                # Transition: Online -> Offline
                was_online = False
                with execution_lock:
                    speaker.speak_no_internet(
                        on_start=display_no_internet_warning,
                        blocking=True
                    )

    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    return thread

def get_prompt_label() -> str:
    """Returns dynamic terminal prompt indicating whether speech output is active or muted."""
    if speaker.is_muted:
        return "[bold cyan]Sky[/bold cyan] [bold yellow]🔇 [MUTED][/bold yellow]"
    return "[bold cyan]Sky[/bold cyan]"

def setup_readline():
    """Configures GNU Readline for slash command tab completion and history."""
    try:
        import readline
        slash_commands = [
            "/help", "/mute", "/unmute", "/sleep",
            "/status", "/tools", "/clear", "/stop", "/exit", "/quit"
        ]
        def completer(text, state):
            matches = [cmd for cmd in slash_commands if cmd.startswith(text)]
            if state < len(matches):
                return matches[state] + " "
            return None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    except Exception:
        pass

def play_startup_greeting():
    """Select a random greeting from the pool, display the welcome panel, and speak it aloud synchronously."""
    greeting = random.choice(STARTUP_GREETINGS)
    speaker.speak(
        greeting,
        on_start=lambda: console.print(Panel(f"[bold green]{greeting}[/bold green]", title="[bold cyan]Sky Welcome[/bold cyan]", border_style="green")),
        blocking=True
    )

def display_banner():
    banner = r"""[bold cyan]
   _____ _  ____     __   
  / ____| |/ /\ \   / /   
 | (___ | ' /  \ \_/ /   
  \___ \|  <    \   /  
  ____) | . \    | |  
 |_____/|_|\_\   |_|                   
[/bold cyan]
[italic dim cyan]Your own assistant[/italic dim cyan]"""
    console.print(Panel(banner, border_style="cyan"))

def display_tools_table():
    tools = registry.get_all_tools()
    table = Table(title="[bold green]Loaded System & Dynamic Tools[/bold green]", border_style="dim")
    table.add_column("Tool Name", style="bold cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Description", style="white")

    core_names = {t.name for t in registry.get_core_tools()}
    for t in tools:
        t_type = "Core" if t.name in core_names else "[bold magenta]Dynamic[/bold magenta]"
        desc = (t.description or "").split("\n")[0][:70]
        table.add_row(t.name, t_type, desc)

    console.print(table)

def display_help_panel():
    """Displays a comprehensive help table of slash commands, voice triggers, and shortcuts."""
    cmd_table = Table(title="[bold cyan]Commands (Type in Terminal)[/bold cyan]", border_style="cyan")
    cmd_table.add_column("Command", style="bold yellow", no_wrap=True)
    cmd_table.add_column("Action", style="white")
    cmd_table.add_column("Shortcut", style="dim cyan")

    cmd_table.add_row("/help", "Show this command guide", "help, /?")
    cmd_table.add_row("/mute", "Silence voice speech (responses show on terminal only)", "mute, /silent, /quiet")
    cmd_table.add_row("/unmute", "Enable voice speech (speaks aloud and shows on terminal)", "unmute, /voice, /speak")
    cmd_table.add_row("/sleep", "Put PC / laptop to sleep (system suspend)", "sleep, suspend, /sleep")
    cmd_table.add_row("/status", "Display laptop battery, CPU, RAM, and disk status", "status, /sys")
    cmd_table.add_row("/tools", "List all active core and dynamic agent tools", "tools, /list")
    cmd_table.add_row("/clear", "Clear the terminal screen and redisplay banner", "clear, cls")
    cmd_table.add_row("/stop", "Terminate Sky assistant process and close terminal", "/exit, /quit, stop")

    voice_table = Table(title="[bold green]Voice Triggers (Speak to Microphone)[/bold green]", border_style="green")
    voice_table.add_column("Action", style="bold yellow")
    voice_table.add_column("Voice Triggers & Examples", style="white")

    voice_table.add_row("Wake & Command", "'Hey Sky...', 'Wake up Sky...', or say any sentence with 'Sky'")
    voice_table.add_row("Mute Output", "'Stop speaking', 'Dont speak', 'Be quiet', 'Silent mode'")
    voice_table.add_row("Unmute Output", "'Start speaking', 'Speak again', 'Unmute', 'Enable voice'")
    voice_table.add_row("Sleep PC", "'Go to sleep', 'Put PC to sleep', 'Sleep'")
    voice_table.add_row("Stop Sky", "'Call it a day', 'Sky stop', 'Rest', 'Take rest'")

    task_table = Table(title="[bold magenta]Example Assistant Tasks (Talk or Type)[/bold magenta]", border_style="magenta")
    task_table.add_column("Category", style="bold cyan")
    task_table.add_column("Examples", style="white")

    task_table.add_row("Apps & System", "'open vs code', 'open chrome', 'check laptop battery and ram'")
    task_table.add_row("Code & Files", "'write add code in python', 'write hello world code in python'")
    task_table.add_row("Memory", "'remember that my favorite language is Python', 'who am I?'")

    console.print(cmd_table)
    console.print(voice_table)
    console.print(task_table)

def handle_slash_command(raw_cmd: str) -> bool:
    """
    Handles terminal slash commands and shortcuts.
    Returns True if intercepted and handled, False otherwise.
    """
    cmd = raw_cmd.strip()
    if not cmd:
        return False

    cmd_lower = cmd.lower()

    # /mute
    if cmd_lower in ("/mute", "mute", "/silent", "silent", "/silence", "silence", "/quiet", "quiet"):
        speaker.mute()
        console.print(Panel(
            "[bold yellow]🔇 Speech Output Muted[/bold yellow]\n\n"
            "[white]Sky is now running in silent mode.[/white]\n"
            "[dim]Voice output is turned off. All answers will appear as text on this terminal only.\n"
            "Notice: Your prompt is now marked with [bold yellow]🔇 [MUTED][/bold yellow] to indicate silent mode.\n"
            "To unmute at any time, type [bold cyan]/unmute[/bold cyan] or say [italic]'start speaking'[/italic].[/dim]",
            title="[bold yellow]Mute Active[/bold yellow]",
            border_style="yellow"
        ))
        return True

    # /unmute
    if cmd_lower in ("/unmute", "unmute", "/voice", "voice", "/speak", "speak"):
        speaker.unmute()
        console.print(Panel(
            "[bold green]🔊 Speech Output Enabled[/bold green]\n\n"
            "[white]Sky will speak responses aloud as well as displaying them on the terminal.[/white]",
            title="[bold green]Voice Enabled[/bold green]",
            border_style="green"
        ))
        speaker.speak("Voice output enabled! I am at your service.", blocking=False)
        return True

    # /help
    if cmd_lower in ("/help", "help", "/?", "?", "-h", "--help"):
        display_help_panel()
        return True

    # /status
    if cmd_lower in ("/status", "status", "/sys", "sys"):
        from sky.tools.core.system_ops import get_system_status
        status_info = get_system_status.invoke({})
        speech_mode = "[bold yellow]🔇 Muted (Voice OFF)[/bold yellow]" if speaker.is_muted else "[bold green]🔊 Enabled (Voice ON)[/bold green]"
        full_status = f"{status_info}\nSpeech Output: {speech_mode}"
        console.print(Panel(full_status, title="[bold cyan]Laptop System Status[/bold cyan]", border_style="cyan"))
        return True

    # /tools
    if cmd_lower in ("/tools", "tools", "/list", "list"):
        display_tools_table()
        return True

    # /clear
    if cmd_lower in ("/clear", "clear", "cls"):
        os.system("clear")
        display_banner()
        return True

    # /sleep
    if cmd_lower in ("/sleep", "sleep", "/suspend", "suspend", "go to sleep", "put pc to sleep"):
        from sky.voice.wake_word import handle_pc_sleep_command
        handle_pc_sleep_command()
        return True

    # /stop
    if cmd_lower in ("/stop", "stop", "/exit", "exit", "/quit", "quit", "call it a day", "sky stop", "stop sky", "rest", "take a rest"):
        from sky.voice.wake_word import handle_stop_command
        handle_stop_command()
        return True

    # Unknown slash command: explicitly say and print that it's not understood
    if cmd.startswith("/"):
        msg = f"I didn't understand the command '{cmd}'. Type /help to see all commands."
        console.print(f"[bold red]{msg}[/bold red]")
        speaker.speak(f"I didn't understand the command {cmd}. Type help to see all commands.", blocking=False)
        return True

    return False

def run_agent_task(task_text: str):
    """Executes a user command through the Sky LangGraph dual-agent pipeline."""
    if not task_text.strip():
        return

    from sky.voice.wake_word import (
        is_stop_phrase,
        handle_stop_command,
        is_pc_sleep_phrase,
        handle_pc_sleep_command,
        check_and_handle_voice_commands,
    )
    
    # Check mute/unmute commands first
    if check_and_handle_voice_commands(task_text):
        return

    # Check PC sleep phrases (puts laptop to sleep via systemctl suspend, keeping Sky alive on wake)
    if is_pc_sleep_phrase(task_text):
        handle_pc_sleep_command()
        return

    # Check program shutdown/stop phrases
    if is_stop_phrase(task_text):
        handle_stop_command()
        return

    # Check internet connectivity before attempting AI coordination
    from sky.config import is_internet_available
    if not is_internet_available():
        speaker.speak_no_internet(on_start=display_no_internet_warning, blocking=True)
        return

    console.print(f"\n[bold yellow]User Command:[/bold yellow] [bold white]{task_text}[/bold white]")

    initial_state = {
        "messages": [HumanMessage(content=task_text)],
        "user_task": task_text,
        "missing_tool_request": None,
        "tool_build_attempts": 0,
        "built_tools": [],
        "last_build_error": None,
    }

    try:
        with console.status("[bold cyan]Sky is coordinating agents...[/bold cyan]", spinner="dots"):
            final_state = initial_state
            for event in sky_graph.stream(initial_state, stream_mode="updates"):
                for node_name, updates in event.items():
                    if node_name == "executor":
                        msgs = updates.get("messages", [])
                        if msgs:
                            last = msgs[-1]
                            if isinstance(last, AIMessage) and last.tool_calls:
                                for tc in last.tool_calls:
                                    if tc["name"] == "request_toolbuilder_build_tool":
                                        console.print(f"\n[bold red][Executor][/bold red] Missing tool detected: [yellow]{tc['args'].get('tool_name')}[/yellow]!")
                                        console.print(f"[dim]Dispatching request to Toolbuilder Agent...[/dim]")
                                    else:
                                        console.print(f"\n[bold blue][Executor Action][/bold blue] Calling tool: [cyan]{tc['name']}[/cyan] with {tc.get('args')}")
                    elif node_name == "toolbuilder":
                        req = updates.get("missing_tool_request", {})
                        code = req.get("code", "")
                        tool_name = req.get("tool_name", "custom_tool")
                        console.print(f"\n[bold magenta][Toolbuilder Agent][/bold magenta] Synthesizing new tool: [bold]{tool_name}[/bold]")
                        if code:
                            syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
                            console.print(Panel(syntax, title=f"Generated Code: {tool_name}.py", border_style="magenta"))
                    elif node_name == "register_tool":
                        err = updates.get("last_build_error")
                        if err:
                            console.print(f"[bold red][Tool Registration Failed]:[/bold red] {err}")
                        else:
                            console.print(f"[bold green][Toolbuilder][/bold green] Tool successfully verified, saved, and loaded into active registry!")
                    elif node_name == "tool_execution":
                        msgs = updates.get("messages", [])
                        for m in msgs:
                            if isinstance(m, ToolMessage):
                                content_preview = m.content[:250] + ("..." if len(m.content) > 250 else "")
                                console.print(f"[dim green]✓ [Tool Result - {m.name}]:[/dim green] {content_preview}")

                    final_state = {**final_state, **updates}
    except Exception as e:
        from sky.config import is_internet_available
        if not is_internet_available() or any(w in str(e).lower() for w in ["connection", "connect", "network", "offline", "unreachable"]):
            speaker.speak_no_internet(on_start=display_no_internet_warning, blocking=True)
            return
        err_msg = "I didn't quite understand that command Omkar, could you please repeat or clarify?"
        panel_title = "[bold cyan]Sky Response[/bold cyan] [bold yellow]🔇 [Muted][/bold yellow]" if speaker.is_muted else "[bold cyan]Sky Response[/bold cyan]"
        console.print(Panel(err_msg, title=panel_title, border_style="yellow" if speaker.is_muted else "cyan"))
        speaker.speak(err_msg, blocking=True)
        return

    # Extract final response from executor
    messages = final_state.get("messages", [])
    response_text = ""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content and not m.tool_calls:
            response_text = m.content
            break

    if not response_text:
        # Check if any AIMessage contained text
        for m in reversed(messages):
            if isinstance(m, AIMessage) and m.content:
                response_text = m.content
                break

    if not response_text:
        response_text = "I didn't quite understand that command Omkar. Could you please clarify what you'd like me to do?"

    # Record interaction to persistent memory
    try:
        from sky.memory.store import memory_store
        memory_store.log_interaction(task_text, response_text)
    except Exception:
        pass

    # Display output panel and speak
    if speaker.is_muted:
        panel_title = "[bold cyan]Sky Response[/bold cyan] [bold yellow]🔇 [Muted][/bold yellow]"
        console.print(Panel(response_text, title=panel_title, border_style="yellow"))
    else:
        panel_title = "[bold cyan]Sky Response[/bold cyan]"
        speaker.speak(
            response_text,
            on_start=lambda: console.print(Panel(response_text, title=panel_title, border_style="cyan")),
            blocking=True
        )

def start_hybrid_mode(greet: bool = True):
    """
    Hybrid Startup Mode:
    Clean interface without instruction walls. Runs background voice listener,
    with an immediate interactive typing prompt. Omkar can talk or type anytime.
    """
    setup_readline()

    from sky.config import is_internet_available
    initial_online = is_internet_available()

    if not initial_online:
        speaker.speak_no_internet(on_start=display_no_internet_warning, blocking=True)
    elif greet:
        play_startup_greeting()

    execution_lock = threading.Lock()

    # Launch background network monitor to auto-detect reconnection or disconnects
    start_network_monitor(execution_lock, initial_online=initial_online, interval_seconds=3.0)

    def on_voice_task(voice_command: str):
        with execution_lock:
            console.print(f"\n[bold cyan]🎙️ [Voice Detected]:[/bold cyan] [bold white]{voice_command}[/bold white]")
            run_agent_task(voice_command)

    # Start background voice listener thread
    from sky.voice.wake_word import WakeWordDetector
    detector = WakeWordDetector(on_wake_callback=on_voice_task)
    voice_thread = threading.Thread(target=lambda: detector.start_listening(verbose=False), daemon=True)
    voice_thread.start()

    while True:
        try:
            cmd = Prompt.ask(get_prompt_label()).strip()
            if not cmd:
                continue

            # Process slash commands first
            if handle_slash_command(cmd):
                continue

            # Process task through agent pipeline with thread lock
            with execution_lock:
                run_agent_task(cmd)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Sky shutting down. Goodbye Omkar![/yellow]")
            break

def interactive_chat_mode():
    """Text-based interactive prompt mode."""
    setup_readline()
    display_tools_table()

    while True:
        try:
            cmd = Prompt.ask(get_prompt_label()).strip()
            if not cmd:
                continue
            
            if handle_slash_command(cmd):
                continue
            
            run_agent_task(cmd)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Exiting Sky.[/yellow]")
            break

def start_voice_mode(greet: bool = False):
    """Voice listener mode with wake-word detection."""
    from sky.voice.wake_word import WakeWordDetector
    from sky.config import is_internet_available

    if not is_internet_available():
        speaker.speak_no_internet(on_start=display_no_internet_warning, blocking=True)
    elif greet:
        play_startup_greeting()

    detector = WakeWordDetector(on_wake_callback=run_agent_task)
    console.print("[bold green]Voice Assistant is Active![/bold green]")
    
    try:
        detector.start_listening()
    except KeyboardInterrupt:
        detector.stop()
        console.print("\n[yellow]Voice mode stopped.[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="Sky AI - Dual-Agent Autonomous Desktop Assistant")
    parser.add_argument("--voice", "-v", action="store_true", help="Start in voice listening mode with wake-word detection")
    parser.add_argument("--chat", "-c", action="store_true", help="Start in text chat mode")
    parser.add_argument("--greet", "-g", action="store_true", help="Play random spoken startup greeting on launch")
    parser.add_argument("--autostart", action="store_true", help="Run in login boot autostart mode")
    parser.add_argument("--task", "-t", type=str, help="Run a single task directly and exit")
    parser.add_argument("--list-tools", action="store_true", help="List all available tools and exit")
    args = parser.parse_args()

    display_banner()

    if args.list_tools:
        display_tools_table()
        return

    # Validate environment
    valid, msg = validate_environment()
    if not valid:
        console.print(Panel(f"[bold red]Configuration Missing:[/bold red] {msg}\n\nPlease edit [bold yellow].env[/bold yellow] file in this directory and add your [bold cyan]GROQ_API_KEY[/bold cyan].\nGet a key for free at [underline blue]https://console.groq.com/keys[/underline blue]", border_style="red"))
        try:
            entered_key = Prompt.ask("[bold yellow]Or paste your GROQ_API_KEY now (press Enter to skip)[/bold yellow]").strip()
            if entered_key:
                from sky.config import PROJECT_ROOT
                with open(PROJECT_ROOT / ".env", "r") as ef:
                    content = ef.read()
                content = content.replace("GROQ_API_KEY=", f"GROQ_API_KEY={entered_key}")
                with open(PROJECT_ROOT / ".env", "w") as ef:
                    ef.write(content)
                console.print("[green]Saved GROQ_API_KEY to .env![/green]")
                import os
                os.environ["GROQ_API_KEY"] = entered_key
            else:
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            sys.exit(1)

    if args.task:
        run_agent_task(args.task)
        return

    if args.autostart:
        start_hybrid_mode(greet=True)
        return

    if args.chat:
        interactive_chat_mode()
        return

    if args.voice:
        start_voice_mode(greet=args.greet)
        return

    # Default to hybrid mode (both talking and typing enabled)
    start_hybrid_mode(greet=args.greet)

if __name__ == "__main__":
    main()
