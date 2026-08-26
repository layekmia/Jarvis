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
