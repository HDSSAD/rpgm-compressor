import os, sys, subprocess, shutil, json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from functools import partial
from concurrent.futures import ThreadPoolExecutor

def clear_screen():
    """ Just a function to clear screen """
    cmd = "cls" if os.name == "nt" else "clear"
    subprocess.run(cmd, shell=True, check=False)
clear_screen()

# Quizá crear una excepción adecuadamente en vez de recurrir a una función
def log_exception(e:Exception, exception_source:str = "Unknown", msg:str = "None", file:Path|None = None):
    """ Función que se lanza cuando ocurre una excepción.

    Guarda un registro con la función donde ocurrió la excepción y un mensaje dentro de la carpeta logs del programa """

    print(f"Ocurrió un error inesperado en: {exception_source}")
    print(f"Mensaje de error: \n {e}")
    with open(f"{get_logs_folder()}/error_{exception_source}.log", "a") as f:
        if file != None:
            print(f"Archivo afectado: {file}")
            f.write(f"Error Source:{exception_source}\nError Message: {msg}\nException Message: {e}\n")
        else:
            f.write(f"Error Source:{exception_source}\nError Message: {msg}\nAffected file: {file}\nException Message: {e}\n")

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

def select_folder(folder_type: str) -> Path|None:
    """ Abre la ventana de dialogo de selección de directorios """
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_folder = filedialog.askdirectory(title=f"Selecciona la carpeta de {folder_type} o cancela para omitir")
    tk_root.destroy()
    if len(selected_folder) == 0:
        return None
    return Path(selected_folder)

def select_file(project_folder:Path, file_name:str, extension:str) -> Path|None:
    """ Abre la ventana de dialogo de selección de archivos """
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_file = filedialog.askopenfilename(title=f"Selecciona el archivo {file_name} correspondiente", filetypes=[(f"{extension}",f"{extension}")], initialdir=str(project_folder))
    tk_root.destroy()
    if len(selected_file) == 0:
        return None
    return Path(selected_file)

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

def nwjs_processing_allowed(project_folder:Path|None):
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a NW.js """
    if nwjs_available() and project_folder != None:
        return True
    else:
        return False

def get_folder_size(folder:Path) -> float:
    """ Recorre una carpeta y devuelve el peso en MB de todo su contenido """
    size = sum(file.stat().st_size for file in folder.rglob('*') if file.is_file())
    size = round(size/1000000, ndigits=2)
    return size

def get_script_folder() -> Path:
    """ Devuelve la ruta actual del programa """
    return Path(__file__).parent

def get_logs_folder() -> Path:
    """ Devuelve la ruta hacia la carpeta logs del programa """
    logs_folder = get_script_folder()/"logs"
    if not logs_folder.exists():
        logs_folder.mkdir(parents=True, exist_ok=True)
    return logs_folder

def get_game_launch_file() -> Path:
    """ Devuelve la ruta hacia el lanzador del juego junto al programa """
    return get_script_folder()/"nwjs_game_launch.bat"

def get_compressed_folder() -> Path:
    """ Devuelve la ruta de la carpeta compressed del programa, y la crea si no existe """
    compressed_folder = get_script_folder()/"compressed"
    if not compressed_folder.exists():
        compressed_folder.mkdir(parents=True, exist_ok=True)
    return compressed_folder

def get_cpu_threads() -> int:
    """ Devuelve la cantidad máxima de nucleos disponibles en la PC menos 1 """
    cpu_cores = os.cpu_count()
    if cpu_cores is None:
        # No se pudo detectar, por defecto solo usamos 1 hilo
        return 1
    else:
        # La cantidad de hilos de procesamiento serán la cantidad de nucleos - 1
        return max(1, cpu_cores -1)

def get_default_image_profile_name() -> str:
    """ Devuelve el nombre de perfil de compresión de imágenes por defecto a usar el el programa"""
    return "PERFORMANCE"

def get_default_cwebp_flags() -> list[str]:
    """ Devuelve los flags de cwebp que corresponden al perfil por defecto para la compresión de imágenes """
    return ["cwebp", "-q", "80", "-alpha_q", "100", "-exact", "-f", "30", "-af", "-quiet"]

def get_video_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos de video que el propgrama procesasará """
    return (".mp4", ".webm", ".avi", ".mkv", ".mov")

def get_audio_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos de audio que el propgrama procesasará """
    return (".ogg", ".mp3", ".wav", ".m4a", ".flac")

def get_image_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos de imagenes que el propgrama procesasará """
    return (".jpg", ".jpeg", ".webp", ".png")

def get_useless_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos consideradas sin utilidad que el propgrama podría eliminar """
    # TODO
    return (".psd",)

def get_encrypted_extensions() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las extensiónes de archivos encriptados """
    # TODO
    return (".rpgmvp", ".rpgmvm", ".rpgmvo",   # RPGM MV
            ".rpgmzp", ".rpgmzm", ".rpgmzo",   # RPGM MZ
            "ogg_", "m4a_", "wav_", "mp3_",    # Otros posibles archivos de audio cifrados
            "jpg_", "jpeg_", "png_", "webp_")  # Otros posibles archivos de imagen cifrados

def get_nwjs_files() -> tuple[str,...]:
    """ Devuelve una tupla que contiene los archivos de NW.js a buscar en la carpeta del juego seleccionado """
    return ("credits.html", "d3dcompiler_47.dll",
            "ffmpeg.dll", "icudtl.dat", 
            "libEGL.dll", "libGLESv2.dll", 
            "node.dll", "nw.dll",
            "nw_100_percent.pak", "nw_200_percent.pak", 
            "nw_elf.dll", "resources.pak", 
            "debug.log", "natives_blob.bin", 
            "snapshot_blob.bin", "v8_context_snapshot.bin",
            "notification_helper.exe", "vulkan-1.dll",
            "vk_swiftshader_icd.json", "vk_swiftshader.dll")

def get_nwjs_folders() -> tuple[str,...]:
    """ Devuelve una tupla que contiene las carpetas de NW.js a buscar en la carpeta del juego seleccionado """
    return ("locales", "swiftshader")

def delete_folder_content(folder:Path):
    """ Toma un directorio elimina todo su contenido """
    if folder.exists():
        folder_content = list(folder.iterdir())
        for item in folder_content:
            if item.is_dir():
                try:
                    shutil.rmtree(item, ignore_errors=True)
                    print(f"Eliminado directorio: {item.name} de {item.parent}")
                except Exception as e:
                    log_exception(e, "delete_folder_content", "rmtree in delete_folder", folder)
            else:
                try:
                    item.unlink()
                except Exception as e:
                    log_exception(e, "delete_folder_content", "file unlink", item)

def delete_files_in_list(folder: Path, files_to_remove: tuple[str,...]) -> float:
    """ Toma un directorio y una lista, busca en el directorio los archivos que se encuentren en la lista y los elimina """
    files_size:float = 0.0
    for root, _, files in folder.walk():
        for file in files:
            if file in files_to_remove:
                file_path = Path(root/file)
                if file_path.exists():
                    try:
                        files_size += file_path.stat().st_size
                        file_path.unlink()
                        print(f"Eliminado: {file_path.relative_to(folder.parent)}")
                    except Exception as e:
                        log_exception(e, "delete_files_in_list", "file unlink", file_path)
    return files_size

def delete_folders_in_list(folder: Path, folders_to_remove: tuple[str,...]) -> float:
    """ Toma un directorio y una lista, busca en el directorio los nombres de directorios que se encuentren en la lista y los elimina """
    folder_size:float = 0.0
    for root, dirs, _ in folder.walk():
        for dir in dirs:
            if dir in folders_to_remove:
                current_folder = (root/dir)
                if current_folder.exists():
                    folder_size += get_folder_size(current_folder)
                    try:
                        shutil.rmtree(current_folder, ignore_errors=True)
                        print( f"Eliminado directorio: {current_folder}")
                    except Exception as e:
                        log_exception(e, "delete_folders_in_list", "rmtree in delete_folder", current_folder)
    return folder_size

def get_localappdata() -> Path|None:
    """ Devuelve un Path con la dirección de la carpeta ~/AppData/Local, y si no la encuentra devuelve un Path vacio """
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata == None:
        return None
    return Path(local_appdata)

def setup_nwjs_game_launcher(project_folder: Path):
    """ Realiza la instalación y configuración del launcher personalizado del juego:

     - Crea un directorio para el perfil del juego en una carpeta específica en Local AppData que será la carpeta universal para todos los juegos.

     - Modifica el archivo de configuración json del juego para usar la carpeta creada anteriormente como perfil.

     - Instala el archivo .bat del launcher personalizado dentro de la caerpeta del juego """
    local_appdata = get_localappdata()
    if local_appdata == None:
        print("Selecciona la carpeta Local que está dentro de AppData")
        print("Usualmente en: C:/Users/(tu usuario)/AppData/Local")
        local_appdata = select_folder("Local AppData")
        if local_appdata == None or local_appdata.name != "Local":
            return
        elif local_appdata.parent.name != "AppData" and not (local_appdata.parent/"LocalLow").exists() and not (local_appdata.parent/"Roaming").exists():
            return
        
    local_appdata= Path(local_appdata)
    rpgm_user_profile = local_appdata/"RPGM/User Data"
    
    # Si no existe carpeta de perfil, la creamos
    if not rpgm_user_profile.exists():
        rpgm_user_profile.mkdir(parents=True, exist_ok=True)

    # Borrar todos los archivos en rpgm_user_profile
    if rpgm_user_profile.exists():
        delete_folder_content(rpgm_user_profile)

    # Update package.json
    package_json_path = project_folder / "package.json"
    if not package_json_path.exists():
        package_json_path = project_folder / "www" / "package.json"
        if not package_json_path.exists():
            input("No se encontró package.json en el proyecto. Asegúrate de seleccionar la carpeta correcta del proyecto")
            return
    try:
        with package_json_path.open("r", encoding="utf-8") as package_file:
            json_changed = False
            package_data = json.load(package_file)
        if package_data.get("name") != "RPGM":
            package_data["name"] = "RPGM"
            json_changed = True
        if "window" not in package_data:
            package_data["window"] = {}
            json_changed = True
        if package_data.get("window").get("position") != "center":
            package_data["window"]["position"] = "center"
            json_changed = True
        if json_changed:
            shutil.copy(package_json_path, package_json_path.with_suffix(".backup.json"))
            with package_json_path.open("w", encoding="utf-8") as package_file:
                json.dump(package_data, package_file, indent=4, ensure_ascii=False)
    except json.JSONDecodeError as e:
        log_exception(e, "setup_nwjs_game_launcher", "json decode", package_json_path)
    except Exception as e:
        log_exception(e,"setup_nwjs_game_launcher", "unknown json error", package_json_path)
    # Update package.json END

    nwjs_game_launcher = get_script_folder() / "nwjs_game_launch.bat"
    if not nwjs_game_launcher.exists():
        print("[X] No se encontró el script de lanzamiento del juego con NW.js del sistema")
        print("[X] Asegúrate de que nwjs_game_launch.bat esté en la misma carpeta que este script")
        return
    else:
        # Copiamos el archivo nwjs_game_launch.bat a la carpeta del proyecto
        try:
            shutil.copy(nwjs_game_launcher, project_folder / "nwjs_game_launch.bat")
            print(f"[+] Script de NWJS Game Launcher copiado a {project_folder}")
        except Exception as e:
            log_exception(e, "setup_nwjs_game_launcher", "shutil copy error", nwjs_game_launcher)
# END of function install_nwjs_game_launch()

def get_audio_hz(project_folder:Path, file: Path) -> int:
    """ Analiza un archivo de audio con ffprobe y devuelve sus hz o 0 si hay error """
    command_ffprobe = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        f"{file}"
    ]
    try:
        result = subprocess.run(command_ffprobe, capture_output=True, text=True)
        hz = int(result.stdout.strip())
    except Exception:
        hz = 0
    # end try
    return hz

def mark_as_optimized(media_file:Path) -> bool:
    """ Copia el flujo de datos (sin recodificar) y añade el tag BROPTIMIZADO.
    """
    output = media_file.with_stem(f"{media_file.stem}_broptimized")
    command:list[str] = [
        "ffmpeg", "-y", "-i", str(media_file),
        "-c", "copy",                        # Copia exacta de audio/video/imagen
        "-map_metadata", "0",                # Mantiene metadatos originales
        "-metadata", "comment=BROPTIMIZADO", # Añade la marca
        str(output)
    ]
    try:
        subprocess.run(command, capture_output=True, text=True)
        output.rename(media_file)
        return True
    except Exception as e:
        # TODO
        print("ERROR", e)
    # end try
    return False
# END of function mark_as_optimized()

def compare_and_replace(original:Path, compressed:Path) -> bool:
    """ Compara dos archivos en directorios diferentes:
    * Si original es más pesado, lo reemplaza por compressed y marca compressed
    * Si original es más ligero, elimina compressed y marca original
    """
    if compressed.exists() and original.exists():
        if compressed.stat().st_size < original.stat().st_size:
            try:
                original.unlink()
                mark_as_optimized(compressed)
                shutil.move(compressed, original.parent)
            except Exception as e:
                # TODO
                print("ERROR",e)
        else:
            try:
                mark_as_optimized(original)
                compressed.unlink()
            except Exception as e:
                # TODO
                print("ERROR",e)
    return True
# END of function compare_and_replace()

def is_optimized(file:Path)-> bool:
    """ Verifica la existencia del string "BROPTIMIZADO" dentro del tag comment en un archivo
    """
    if file.exists():
        command:list[str] = [
            "ffprobe", "-v", "-quiet",
            "-show_entries", "format_tags=comment",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file)
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            return "BROPTIMIZADO" in result.stdout
        except Exception as e:
            # TODO
            print("ERROR",e)
    return False
# END of function is_optimized()

def compress_image(project_folder:Path, cwebp_flags:list[str], source:Path):
    # Output será un webp disfrazado de png (u otra extensión del archivo original)
    # para facilitar la aceptación del archivo por parte del motor de RPG Maker y sus scripts
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = get_compressed_folder()/rel_source
        command:list[str] = cwebp_flags.copy()
        command.append(f"{source}")
        command.append("-o")
        command.append(f"{output}")
        if len(command) > 0:
            try:
                print(f"Procesando: {source.relative_to(project_folder)}")
                subprocess.run(command)
            except Exception as e:
                # TODO
                print("ERROR",e)

            compare_and_replace(source, output)
# END of function compress_image()

def compress_audio(project_folder:Path, source:Path):
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = get_compressed_folder()/rel_source
        output = output.with_suffix(".ogg")
        hz = get_audio_hz(project_folder, source)
        if 22050 <= hz < 32000:
            hz = 22050
        else:
            hz = 32000
        command:list[str] = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", f"{source}",
                "-c:a", "libvorbis", 
                "-ar", f"{hz}", 
                "-q:a", "0", 
                "-y", f"{output}"
            ]
        if len(command) > 0:
            try:
                print(f"Procesando: {source.relative_to(project_folder)}")
                subprocess.run(command)
            except Exception as e:
                # TODO
                print("ERROR",e)

            compare_and_replace(source, output)
# END of function compress_audio()

def compress_video(project_folder:Path, quality:int, plus:int|float, source:Path):
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = get_compressed_folder()/rel_source.with_suffix(".mp4")
        target_res, video_bitrate, vf_scale = optimal_video_quality(source, quality, plus)

        if min(target_res, video_bitrate) == 0 or vf_scale == "":
            return False
        
        audio_bitrate = "48"
        audio_codec = "libopus"
        extra = ["-pix_fmt", "yuv420p", "-ar", "48000", "-tune", "animation"]
        video_codec = "libx264"

        passlog = "ffmpeg_pass_temp"
        null = "NUL" if os.name == "nt" else "/dev/null"

        cmd1:list[str] = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", str(source),
            "-vf", f"scale={vf_scale}",
            "-c:v", video_codec,
            "-preset", "medium",
            *extra,
            "-b:v", f"{video_bitrate}k",
            "-pass", "1",
            "-passlogfile", passlog,
            "-an", "-f", "null", null
        ]
        try:
            subprocess.run(cmd1, check=True)
        except subprocess.CalledProcessError as e:
            print("Falló Pass 1", e)
            return False
        # end try

        # Pass 2
        cmd2:list[str] = [
            "ffmpeg", "-i", str(source),
            "-vf", f"scale={vf_scale}",
            "-c:v", video_codec,
            "-preset", "medium",
            *extra,
            "-b:v", f"{video_bitrate}k",
            "-pass", "2",
            "-passlogfile", passlog,
            "-c:a", audio_codec,
            "-b:a", f"{audio_bitrate}k",
            "-y", str(output)
        ]
        try:
            subprocess.run(cmd2, check=True)
        except subprocess.CalledProcessError as e:
            print("Falló Pass 2", e)
            return False
        # end try

        compare_and_replace(source, output)

        # Limpieza
        for passlog_file in [f"{passlog}-0.log", f"{passlog}-0.log.mbtree"]:
            passlog_file = Path(passlog_file)
            if passlog_file.is_file():
                passlog_file.unlink()
        return True
# END of function compress_video()

def optimal_video_quality(source:Path, quality:int, plus:int|float) -> tuple[int, int, str]:
    """ Recibe un video y devuelve su resolución y bitrate optimos junto con su escala
    * source: Path que apunta a un archivo de video
    * quality: lado más pequeño de resolución deseada
    * plus: umbral de calidad
    """
    width, height = get_video_resolution(source)
    original_res:int = min(width, height)
    if original_res == 0:
        return 0,0,""
    
    target_res:int = min(original_res, quality)
    if width > height:
        vf_scale = f"-2:{target_res}"
    else:
        vf_scale = f"{target_res}:-2"

    original_kbps:int = get_video_kbps(source)
    target_optimal_kbps:int = optimal_kbps_for_resolution(target_res, plus)
    original_optimal_kbps:int = optimal_kbps_for_resolution(original_res, plus)

    if original_kbps == 0:
        return target_res, target_optimal_kbps, vf_scale

    if original_res <= target_res:
        if original_kbps <= original_optimal_kbps:
            return original_res, original_kbps, vf_scale
        else:
            return original_res, original_optimal_kbps, vf_scale
    else:
        ratio:float = original_kbps/original_optimal_kbps
        if ratio >= 1:
            return target_res, target_optimal_kbps, vf_scale
        else:
            return target_res, int(target_optimal_kbps*ratio), vf_scale
# END of function optimal_video_quality()

def get_video_kbps(video_path:Path) -> int:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=bit_rate",
        "-of", "csv=s=x:p=0", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
        result = int(result.stdout.strip())
        return int(result/1000)
        
    except subprocess.CalledProcessError as e:
        print("Error al obtener el bit rate", e)
    except Exception as e:
        print("Ocurrió un error inesperado - get_video_bitrate()", e)
    return 0

def optimal_kbps_for_resolution(quality:int, plus:float|int = 1.15) -> int:
    return int(((quality ** 2 / 180)  - (15/4) * quality + 1020)*plus)

def get_video_resolution(video_path:Path) -> tuple[int, int]:
    """
    Obtiene la resolución de un video usando ffprobe.
    Retorna ancho y alto si se completó con éxito, None si algo falló.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        width, height = result.stdout.strip().split("x")
        return int(width), int(height)
    except subprocess.CalledProcessError as e:
        print("Error al obtener resolución", e.stdout)
        return 0,0
    except Exception as e:
        print("Ocurrió un error inesperado - get_video_resolution()", e)
        return 0,0

def get_source_list(project_folder:Path, extensions:tuple[str,...]) -> list[Path]:
    source_file_list:list[Path] = []
    for root, _, files in project_folder.walk():
        for file in files:
            if file.lower().endswith(extensions):
                source_file = root/file
                if not is_optimized(source_file):
                    source_file_list.append(source_file)
    return source_file_list

def create_output_path(project_folder:Path, source_file_list:list[Path]):
    for source_file in source_file_list:
        rel_source_file = source_file.relative_to(project_folder)
        output_file = get_compressed_folder()/rel_source_file
        if not output_file.parent.exists():
            output_file.parent.mkdir(parents=True, exist_ok=True)

def process_images(project_folder:Path, extensions:tuple[str,...], cwebp_flags:list[str]):
    print("=== Preparando archivos de imágenes ===")
    max_threads = get_cpu_threads()
    source_list = get_source_list(project_folder, extensions)
    if len(source_list) > 0:
        create_output_path(project_folder, source_list)
        print("=== Iniciando procesamiento de imágenes ===")
        with ThreadPoolExecutor(max_threads) as executor:
            executor.map(
                partial(compress_image, project_folder, cwebp_flags),
                source_list
                )
# END of function process_images()

def process_audios(project_folder:Path, extensions:tuple[str,...]):
    print("=== Preparando archivos de audio ===")
    max_threads = get_cpu_threads()
    source_list = get_source_list(project_folder, extensions)
    if len(source_list) > 0:
        create_output_path(project_folder, source_list)
        print("=== Iniciando procesamiento de audios ===")
        with ThreadPoolExecutor(max_threads) as executor:
            executor.map(
                partial(compress_audio, project_folder),
                source_list
                )
# END of function process_audios()

def process_videos(project_folder:Path, extensions:tuple[str,...], quality:int = 600, plus:int|float = 1.15):
    print("=== Preparando archivos de videos ===")
    # Limitación a 1 hilo debido a que el procesamiento de videos es más pesado
    # Se mantiene el formato del código para actualizarlo en el futuro
    max_threads = 1 
    source_list = get_source_list(project_folder, extensions)
    if len(source_list) > 0:
        create_output_path(project_folder, source_list)
        print("=== Iniciando procesamiento de videos ===")
        with ThreadPoolExecutor(max_threads) as executor:
            executor.map(
                partial(compress_video, project_folder, quality, plus),
                source_list
                )
# END of function process_videos()
            
def subfolder_of(folder:Path, parent:Path) -> bool:
    if str(parent) in str(folder):
        return True
    return False

def find_system_json(project_folder:Path) -> Path|None:
    """ Busca el archivo System.json en rutas posibles, 
    o solicita al usuario seleccionar el archivo manualmente si no lo encuentra. 
    
    Si no se encuentra y no se selecciona el archivo válido, devuelve un Path() vacío.
    """
    posible_system_paths = [
        project_folder/"www/data/System.json", 
        project_folder/"data/System.json"
        ]
    for system_json_path in posible_system_paths:
        if system_json_path.exists():
            return system_json_path
    system_json_path = select_file(project_folder, "System.json", ".json")
    if system_json_path != None:
        if system_json_path.name.lower() == "system.json" and subfolder_of(system_json_path, project_folder):
            return system_json_path
    return None
    

def get_json_keyvalue(project_folder:Path, json_path:Path, key:str):
    """ Acepta un Path apuntando a un archivo json.

    Si la key (clave) se encuentra en el archivo json, devuelve el valor de la clave. 

    Si el archivo no existe u ocurre un error al obtener el valor de la key (clave), Lanza una Excepción.
    """        
    try:
        with json_path.open("r", encoding="utf-8") as f:
            json_data = json.load(f)
        value = json_data.get(key)
        return value
    except Exception as e:
        # TODO
        print("[X] ERROR: No se obtuvo el valor correcto de encriptación")
        raise e
            
def update_system_json(project_folder:Path, key_list:list[str], value:bool):
    print("=== Actualizando System.json ===")
    system_json_path = find_system_json(project_folder)
    if system_json_path == None:
        print(f"[X] ERROR: No se ha seleccionado un System.json válido dentro de {project_folder}")
        input("[!] La tarea no puede continuar. Presione una tecla para omitir la actualización de JSON")
        return
    try:
        with system_json_path.open("r", encoding="utf-8") as f:
            json_changed = False
            system_json_data = json.load(f)
        for key in key_list:
            if system_json_data.get(key) != value:
                system_json_data[key] = value
                json_changed = True
        if json_changed:
            shutil.copy(system_json_path, system_json_path.with_suffix(".backup.json"))
            with system_json_path.open("w", encoding="utf-8") as system_json:
                json.dump(system_json_data, system_json, indent=4, ensure_ascii=False)
    except json.JSONDecodeError as e:
        log_exception(e, "update_system_json", "json decode", system_json_path)
    except Exception as e:
        log_exception(e,"update_system_json", "unknown json error", system_json_path)

def get_rpgm_encryption_key(project_folder:Path) -> str|None:
    system_json = find_system_json(project_folder)
    if system_json == None:
        return None
    try:
        encryption_key = get_json_keyvalue(project_folder, system_json, "encryptionKey")
        encryption_key = str(encryption_key)
        if len(encryption_key) == 32:
            return encryption_key
    except Exception as e:
        # TODO
        print("No se ha encontrado la clave de encriptado",e)
        return None


def compare_project_size(original_size:float, new_size:float):
    # Mostrar espacio en disco ahorrado
    print(f"Tamaño del proyecto originalmente: {original_size}MB")
    print(f"Espacio Ahorrado tras la compresión: {round(original_size-new_size, ndigits=2)}MB")
    print(f"Tamaño actual del proyecto: {new_size}MB")

def menu_image_profile(image_profile_name: str, cwebp_flags: list[str]) -> tuple[str, list[str]]:
    cwebp_profiles = {  # indice del perfil : (nombre del perfil, lista de flags para cwebp)
        1: ("PERFORMANCE", ['cwebp', '-q', '80', '-alpha_q', '100', '-exact', '-f', '30', '-af', '-quiet']),
        2: ("MEDIUM", ['cwebp', '-near_lossless', '75', '-alpha_q', '100', '-exact', '-m', '6', '-mt', '-quiet']),
        3: ("QUALITY", ['cwebp', '-lossless', '-z', '9', '-alpha_q', '100', '-exact', '-mt', '-quiet'])
    }
    while True:
        print("\n" + "="*50)
        print("     PERFILES DE COMPRESIÓN DE IMÁGENES")
        print("="*50)
        print(f"Perfil Actual: {image_profile_name}")
        print("1 - Perfil PERFORMANCE   (más pequeño, posible pérdida leve en algunos sprites)")
        print("2 - Perfil MEDIUM        (buen compromiso, casi imperceptible en pixel art)")
        print("3 - Perfil QUALITY       (sin artefactos, recomendado para animaciones y efectos)")
        print("0 - Aceptar cambios y volver al menu principal")
        print("="*50)
        try:
            option_img_profile = input("Elige perfil (1-3) o 0 para volver al menu principal: ").strip()
            option_img_profile = int(option_img_profile)
            if option_img_profile in cwebp_profiles:
                image_profile_name, cwebp_flags = cwebp_profiles[option_img_profile]
            elif option_img_profile == 0:
                print("Volviendo al menú principal...")
                return image_profile_name, cwebp_flags
            else:
                print("Por favor, elige un número entre 0 y 3.")
        except ValueError:
            print("Entrada inválida. Ingresa un número.")
# END of function chose_image_profile

def main_menu(project_folder:Path|None = None):
    image_profile_name:str = get_default_image_profile_name()
    cwebp_flags:list[str] = get_default_cwebp_flags()
    compressed_folder:Path = get_compressed_folder()
    initial_project_size:float = 0.0
    if project_folder != None:
        initial_project_size = get_folder_size(project_folder)
    project_processed:bool = False
    while True:
        print("="*50)
        print("     MENU PRINCIPAL")
        print("="*50)

        if project_folder != None: 
            print(f"Tamaño inicial del proyecto: {initial_project_size}MB", \
                  f"\nTamaño Actual del proyecto: {get_folder_size(project_folder)}MB" if project_processed else "")

        options_range:list[int] = [0,1,2]
        print(f"1 - Seleccionar ruta del proyecto. Actual:", f"{project_folder}" if project_folder != None else "NO SELECCIONADA")
        print(f"2 - Menu opciones de calidad de conversión de imágenes. Preset Actual: {image_profile_name}")
        
        if project_folder != None:
            if image_processing_allowed(project_folder):
                print(f"3 - Iniciar compresión de Imágenes")
                options_range.append(3)
            else: print(f"3 - [X] Compresión de Imágenes no disponible sin cwebp")
            if audio_processing_allowed(project_folder):
                print(f"4 - Iniciar compresión de audio")
                options_range.append(4)
            else: print(f"4 - [X] Compresión de audio no disponible sin ffmpeg y ffprobe")
            if video_processing_allowed(project_folder):
                print(f"5 - Iniciar compresión de video")
                options_range.append(5)
            else: print(f"5 - [X] Compresión de video no disponible sin ffmpeg y ffprobe")
            if image_processing_allowed(project_folder) and audio_processing_allowed(project_folder):
                print(f"6 - Iniciar compresión de imágenes y audio")
                options_range.append(6)
            else: print(f"6 - [X] Compresión de imágenes y audio no disponible sin apps correspondientes")
            if get_game_launch_file().exists() and nwjs_processing_allowed(project_folder):
                print(f"7 - Instalar y configurar {get_game_launch_file().name}")
                options_range.append(7)
            else: print(f"7 - [X] No se puede Instalar y configurar {get_game_launch_file().name} si el archivo no existe junto a este script")
            print(f"8 - Limpiar NW.js local del directorio del proyecto")
            options_range.append(8)
        print("9 - Borrar logs")
        options_range.append(9)
        print("0 - Salir del programa")

        try:
            option_main = input(f"Elige una opción {str(options_range)}: ").strip()
            print("") # Solo para tener una lína vacia bajo la selección
            option_main = int(option_main)
            if option_main in options_range:
                if option_main == 0:
                    break
                elif option_main == 1:
                    print("Seleccionando directorio del proyecto")
                    new_project_folder = select_folder("Proyecto")
                    if new_project_folder != project_folder and new_project_folder != None:
                        delete_folder_content(compressed_folder)
                        project_folder = new_project_folder
                        initial_project_size = get_folder_size(project_folder)
                        project_processed = False
                elif project_folder != None:
                    if option_main == 2:
                        image_profile_name, cwebp_flags = menu_image_profile(image_profile_name, cwebp_flags)
                    elif option_main == 3:
                        print("Ejecutando tarea de compresión de imágenes...")
                        process_images(project_folder, get_image_extensions(), cwebp_flags)
                        update_system_json(project_folder, ["hasEncryptedImages"], False)
                        compare_project_size(initial_project_size, get_folder_size(project_folder))
                        delete_folder_content(compressed_folder)
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 4:
                        print("Ejecutando tarea de compresión de audios...")
                        process_audios(project_folder, get_audio_extensions())
                        update_system_json(project_folder, ["hasEncryptedAudio"], False)
                        compare_project_size(initial_project_size, get_folder_size(project_folder))
                        delete_folder_content(compressed_folder)
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 5:
                        print("Ejecutando tarea de compresión de videos...")
                        process_videos(project_folder, get_video_extensions(), 600)
                        compare_project_size(initial_project_size, get_folder_size(project_folder))
                        delete_folder_content(compressed_folder)
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 6:
                        print("Ejecutando tarea de compresión de archivos de medios...")
                        process_images(project_folder, get_image_extensions(), cwebp_flags)
                        process_audios(project_folder, get_audio_extensions())
                        process_videos(project_folder, get_video_extensions(), 600)
                        update_system_json(project_folder, ["hasEncryptedImages", "hasEncryptedAudio"], False)
                        compare_project_size(initial_project_size, get_folder_size(project_folder))
                        delete_folder_content(compressed_folder)
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 7:
                        print("Preparando el entorno del juego...")
                        setup_nwjs_game_launcher(project_folder)
                        print("nwjs_game_launch instalado y configurado")
                        subprocess.run(f"{project_folder/get_game_launch_file().name}", cwd=f"{project_folder}")
                        print("Juego lanzado")
                    elif option_main == 8:
                        print(f"Borrando archivos de NW.js locales en {project_folder.name}...")
                        delete_files_in_list(project_folder, get_nwjs_files())
                        delete_folders_in_list(project_folder, get_nwjs_folders())
                        print(f"Archivos locales de NW.js eliminados de {project_folder.name}")
                        compare_project_size(initial_project_size, get_folder_size(project_folder))
                        project_processed = True
                elif option_main == 9:
                    print("Borrando logs...")
                    delete_folder_content(get_logs_folder())
            else:
                print(f"Número fuera del rango {str(options_range)}.")

        except ValueError:
            print(f"¡Error! Ingresaste algo que no es un número")
        except Exception as e:
            log_exception(e, "Main Menu")


if any(get_compressed_folder().iterdir()):
    delete_folder_content(get_compressed_folder())
main_menu(select_folder("Proyecto"))

print("=============================================")
print("Programa terminado. Presione enter para salir")
input("=============================================")
sys.exit()

# TODO
# Agregar nuevo menú para manejar archivos encriptados
# Buscar en System.json: hasEncryptedImages, hasEncryptedAudio, y encryptionKey
# Desencriptar archivos y volver a encriptarlos de ser necesario
# Manejar adecuadamente excepciones marcadas con "# TODO"
# Mejorar selección automática de caldiad de video
# Añadir presets de calidad de video
# Añadir conversiín en formato webm
# Probar conversión de audio en opus
# Añadir conversiín de audio en mp3 o wav?
# Añadir instalación de dependencias como NWJS, FFMPEG, y CWEBP?
# Otras cosas más...