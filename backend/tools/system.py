import os
import psutil
from loguru import logger
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def set_volume(level: int) -> str:
    """Sets the system volume to a specific level (0-100)."""
    try:
        level = max(0, min(100, int(level)))
        import comtypes
        comtypes.CoInitialize()
        
        devices = AudioUtilities.GetSpeakers()
        volume = devices.EndpointVolume
        
        # Pycaw uses scalar from 0.0 to 1.0 for volume
        scalar_volume = level / 100.0
        volume.SetMasterVolumeLevelScalar(scalar_volume, None)
        
        logger.success(f"Volume set to {level}%")
        return f"Volume has been set to {level}%."
    except Exception as e:
        logger.error(f"Failed to set volume: {e}")
        return f"Failed to set volume: {str(e)}"

def set_brightness(level: int) -> str:
    """Sets the screen brightness to a specific level (0-100)."""
    try:
        level = max(0, min(100, int(level)))
        sbc.set_brightness(level)
        logger.success(f"Brightness set to {level}%")
        return f"Screen brightness has been set to {level}%."
    except Exception as e:
        logger.error(f"Failed to set brightness: {e}")
        return f"Failed to set brightness: {str(e)}"

def get_system_info() -> str:
    """Returns basic system information (CPU, RAM, Battery)."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        
        info = f"CPU Usage: {cpu}%. RAM Usage: {ram.percent}% ({ram.used / (1024**3):.1f}GB / {ram.total / (1024**3):.1f}GB)."
        
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                plugged = "plugged in" if battery.power_plugged else "on battery"
                info += f" Battery is at {battery.percent}% ({plugged})."
        
        logger.info(f"System info retrieved: {info}")
        return info
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return f"Failed to get system info: {str(e)}"

# Sentinel prefix — mirrors the one in file_tools.py
CONFIRM_PREFIX: str = "CONFIRM_NEEDED:"


def shutdown_system() -> str:
    """
    Returns a CONFIRM_NEEDED sentinel asking the user to confirm shutdown.
    Does NOT immediately shut down.
    """
    logger.warning("Shutdown requested — waiting for user confirmation.")
    return (
        f"{CONFIRM_PREFIX} Are you sure you want to shut down your PC? "
        f"All unsaved work will be lost. "
        f"[action=shutdown_system_confirmed]"
    )


def shutdown_system_confirmed() -> str:
    """Actually executes the shutdown after explicit user confirmation."""
    try:
        os.system("shutdown /s /t 10")
        logger.warning("System shutdown initiated (10s delay).")
        return "Shutting down your PC in 10 seconds."
    except Exception as e:
        logger.error(f"Failed to shutdown system: {e}")
        return f"Failed to shutdown system: {str(e)}"


def restart_system() -> str:
    """
    Returns a CONFIRM_NEEDED sentinel asking the user to confirm restart.
    Does NOT immediately restart.
    """
    logger.warning("Restart requested — waiting for user confirmation.")
    return (
        f"{CONFIRM_PREFIX} Are you sure you want to restart your PC? "
        f"All unsaved work will be lost. "
        f"[action=restart_system_confirmed]"
    )


def restart_system_confirmed() -> str:
    """Actually executes the restart after explicit user confirmation."""
    try:
        os.system("shutdown /r /t 10")
        logger.warning("System restart initiated (10s delay).")
        return "Restarting your PC in 10 seconds."
    except Exception as e:
        logger.error(f"Failed to restart system: {e}")
        return f"Failed to restart system: {str(e)}"
