import os, subprocess, shutil
from pathlib import Path

def clear_screen():
    """ Just a function to clear screen """
    cmd:str = "cls" if os.name == "nt" else "clear"
    subprocess.run(cmd, shell=True, check=False)

def cwebp_available():
    """ Devuelve True si existe cwebp en las variables de entorno del sistema """
    if shutil.which("cwebp"):
        return True
    else:
        return False

def ffprobe_available():
    """ Devuelve True si existe ffprobe en las variables de entorno del sistema """
    if shutil.which("ffprobe"):
        return True
    else:
        return False
    
def ffmpeg_available():
    """ Devuelve True si existe ffmpeg en las variables de entorno del sistema """
    if shutil.which("ffmpeg"):
        return True
    else:
        return False
    
def nwjs_available():
    """ Devuelve True si existe nw en las variables de entorno del sistema """
    if shutil.which("nw"):
        return True
    else:
        return False

def video_processing_allowed(project_folder:Path|None) -> bool:
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a video """
    if ffprobe_available() and ffmpeg_available() and project_folder != None:
        return True
    else:
        return False
    
def audio_processing_allowed(project_folder:Path|None) -> bool:
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a audio """
    if ffprobe_available() and ffmpeg_available() and project_folder != None:
        return True
    else:
        return False
    
def image_processing_allowed(project_folder:Path|None) -> bool:
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a imágenes """
    if cwebp_available() and project_folder != None:
        return True
    else:
        return False

def nwjs_processing_allowed(project_folder:Path|None) -> bool:
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a NW.js """
    if nwjs_available() and project_folder != None:
        return True
    else:
        return False

def get_cpu_threads() -> int:
    """ Devuelve la cantidad máxima de nucleos disponibles en la PC menos 1 """
    cpu_cores: int | None = os.cpu_count()
    if cpu_cores is None:
        # No se pudo detectar, por defecto solo usamos 1 hilo
        return 1
    else:
        # La cantidad de hilos de procesamiento serán la cantidad de nucleos - 1
        return max(1, cpu_cores -1)