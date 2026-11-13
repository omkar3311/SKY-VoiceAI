import os
import platform
import subprocess
from typing import Optional
from langchain_core.tools import tool

@tool
def open_webcam() -> str:
    """
    Open the laptop's default webcam and display the live feed to the user.

    This function attempts to use OpenCV (cv2) if it is available. If OpenCV is
    not installed, it falls back to invoking a system command that plays the
    webcam stream using `ffplay`. The function blocks until the user closes the
    webcam window or presses the designated key to exit.

    Returns:
        str: A message indicating success or describing any error that occurred.
    """
    try:
        # Attempt to use OpenCV first
        try:
            import cv2  # type: ignore
        except Exception:
            cv2 = None

        if cv2:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Error: Unable to access the webcam with OpenCV."
            cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                cv2.imshow("Webcam Feed", frame)
                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            cap.release()
            cv2.destroyAllWindows()
            return "Webcam feed closed successfully."
        else:
            # Fallback to system command using ffplay
            system = platform.system()
            if system == "Windows":
                cmd = [
                    "ffplay",
                    "-f",
                    "dshow",
                    "-i",
                    "video=\"Integrated Camera\"",
                    "-autoexit",
                ]
            elif system == "Darwin":
                # macOS uses avfoundation; device index 0 is usually the built-in camera
                cmd = ["ffplay", "-f", "avfoundation", "-i", "0", "-autoexit"]
            else:  # Assume Linux/Unix
                # Common device path for default webcam
                cmd = ["ffplay", "/dev/video0", "-autoexit"]

            # Check if ffplay is available
            if not shutil.which("ffplay"):
                return "Error: ffplay not found. Install FFmpeg to use the fallback method."

            # Run ffplay in a subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                return f"Error: ffplay failed with exit code {process.returncode}. Stderr: {stderr.strip()}"
            return "Webcam feed closed successfully via ffplay."
    except Exception as e:
        return f"Error opening webcam: {str(e)}"