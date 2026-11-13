import os
import sys
import subprocess
import platform
from typing import Optional
from langchain_core.tools import tool

@tool
def open_webcam_fixed() -> str:
    """
    Open the laptop's default webcam and display the live feed to the user.

    The function first attempts to use OpenCV (cv2) to capture and display the
    webcam stream. If OpenCV is not installed or fails to initialize the
    camera, it falls back to using the `ffplay` command-line utility. The
    function handles platform-specific command arguments for Windows,
    Linux, and macOS.

    Returns:
        A string describing the outcome of the operation. On success it
        indicates that the webcam feed was displayed. On failure it returns
        an informative error message.
    """
    try:
        # Attempt to use OpenCV
        try:
            import cv2  # type: ignore
        except Exception:
            cv2 = None

        if cv2 is not None:
            # Try to open the default camera (index 0)
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("OpenCV: Unable to open webcam (index 0).")
            cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                cv2.imshow("Webcam Feed", frame)
                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()
            return "Success: Webcam feed displayed using OpenCV. Press 'q' to exit."

        # Fallback to ffplay if OpenCV is unavailable
        system = platform.system()
        ffplay_cmd: Optional[list[str]] = None

        if system == "Windows":
            # Windows uses dshow; adjust device name if necessary
            ffplay_cmd = ["ffplay", "-f", "dshow", "-i", "video=Integrated Camera", "-autoexit"]
        elif system == "Linux":
            ffplay_cmd = ["ffplay", "-f", "v4l2", "-i", "/dev/video0", "-autoexit"]
        elif system == "Darwin":
            ffplay_cmd = ["ffplay", "-f", "avfoundation", "-i", "0", "-autoexit"]
        else:
            return f"Error: Unsupported operating system '{system}'."

        # Check if ffplay is available
        try:
            subprocess.run(["ffplay", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            return "Error: ffplay is not installed or not found in PATH."

        # Launch ffplay to display webcam
        process = subprocess.Popen(ffplay_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            return f"Error: ffplay exited with code {process.returncode}. Stderr: {stderr.decode(errors='ignore')}"
        return "Success: Webcam feed displayed using ffplay."

    except Exception as e:
        return f"Error: {str(e)}"