import os
import subprocess
import psutil
from typing import Optional
from langchain_core.tools import tool
from sky.config import WORKSPACE_DIR

@tool
def run_command(command: str, timeout_seconds: int = 30) -> str:
    """
    Execute a shell/terminal command on the laptop and return output.
    
    Args:
        command: The bash command to execute (e.g., 'ls -la', 'python script.py', 'git status').
        timeout_seconds: Maximum execution time before aborting (default 30 seconds).
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(WORKSPACE_DIR)
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        response = [f"Exit code: {result.returncode}"]
        if stdout:
            response.append(f"STDOUT:\n{stdout}")
        if stderr:
            response.append(f"STDERR:\n{stderr}")
        if not stdout and not stderr:
            response.append("(Command executed with no output)")
            
        return "\n".join(response)
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout_seconds} seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

@tool
def speak_to_user(message: str) -> str:
    """
    Speak a verbal message aloud to the user through laptop speakers.
    Use this to talk to the user, give audible status updates, or confirm task completion.
    
    Args:
        message: The sentence or message to speak aloud.
    """
    from sky.voice.speaker import speaker
    speaker.speak(message, blocking=True)
    return f"Spoke aloud to user: '{message}'"

@tool
def put_pc_to_sleep() -> str:
    """
    Puts the laptop or PC to sleep (system suspend).
    Call this when Omkar tells you to 'go to sleep', 'put pc to sleep', 'put laptop to sleep', or suspend the computer.
    """
    from sky.voice.wake_word import handle_pc_sleep_command
    handle_pc_sleep_command()
    return "Laptop put to sleep."

@tool
def stop_sky_assistant(farewell_reason: str = "user request") -> str:
    """
    Gracefully stop and shut down the Sky AI assistant.
    Call this when Omkar tells you to 'call it a day', 'stop', 'rest', 'take rest', 'exit', or shut down.
    
    Args:
        farewell_reason: The reason given for stopping (e.g. 'call it a day', 'rest', 'stop').
    """
    import sys
    from sky.voice.wake_word import handle_stop_command
    handle_stop_command()
    return "Sky assistant stopped."

@tool
def toggle_speech_output(enable: bool) -> str:
    """
    Enable or disable spoken voice output.
    When disabled (enable=False), Sky stops speaking and displays all output purely as text on the terminal.
    When enabled (enable=True), Sky speaks responses aloud as well as displaying them.
    
    Args:
        enable: True to start speaking aloud, False to stop speaking (mute).
    """
    from sky.voice.speaker import speaker
    if enable:
        speaker.unmute()
        speaker.speak("Voice output enabled! I will speak with you again.", blocking=True)
        return "Speech output enabled. Sky will now speak responses aloud and show them on terminal."
    else:
        speaker.speak("Understood Omkar, I will stay quiet and only display text on your terminal.", blocking=True)
        speaker.mute()
        return "Speech output disabled. Sky is now muted and will only display text output on terminal."

@tool
def get_system_status() -> str:
    """
    Get current laptop system status including CPU usage, RAM memory, and battery level.
    """
    try:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        battery = psutil.sensors_battery()
        bat_info = "N/A"
        if battery:
            status = "Plugged in" if battery.power_plugged else "Discharging"
            bat_info = f"{battery.percent:.1f}% ({status})"
            
        info = [
            f"CPU Usage: {cpu_usage}%",
            f"RAM Usage: {memory.percent}% (Used: {memory.used // (1024**2)}MB / Total: {memory.total // (1024**2)}MB)",
            f"Disk Usage: {disk.percent}% free: {disk.free // (1024**3)}GB",
            f"Battery: {bat_info}",
        ]
        from sky.voice.speaker import speaker
        speech_str = "🔇 Muted (Voice OFF)" if speaker.is_muted else "🔊 Active (Voice ON)"
        info.append(f"Speech Mode: {speech_str}")
        return "\n".join(info)
    except Exception as e:
        return f"Error reading system status: {str(e)}"
