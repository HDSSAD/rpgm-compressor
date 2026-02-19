import os, sys, subprocess, shutil, json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from functools import partial
from concurrent.futures import ThreadPoolExecutor

def clear_screen():
    cmd = "cls" if os.name == "nt" else "clear"
    subprocess.run(cmd, shell=True, check=False)
clear_screen()

""" def require_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        print("Ejecutando con privilegios de administrador")
    else:
        # Re-ejecutar el script con derechos de administrador
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f""{__file__}"", None, 1
        )
        sys.exit() """

# Quizá crear una excepción adecuadamente en vez de recurrir a una función
def log_exception(e:Exception, exception_source:str = "Unknown", msg:str = "None",file:Path = Path()):
    print(f"Ocurrió un error inesperado en: {exception_source}")
    if file == Path(): print(f"Archivo afectado: {file}")
    print(f"Mensaje de error: \n {e}")
    with open(f"{get_logs_folder()}/error_{exception_source}.log", "a") as f:
        if file != Path():
            f.write(f"Error Source:{exception_source}\nError Message: {msg}\nException Message: {e}\n")
        else:
            f.write(f"Error Source:{exception_source}\nError Message: {msg}\nAffected file: {file}\nException Message: {e}\n")

def file_log(project_folder:Path, category:str, file_path:Path):
    project_name = project_folder.name
    current_log_path = get_logs_folder()/project_name
    if not current_log_path.exists(): 
        current_log_path.mkdir(parents=True, exist_ok=True)
    with open(f"{current_log_path/category}.log", "a") as f:
        f.write(f"{file_path}")

def cwebp_available():
    if shutil.which("cwebp"):
        return True
    else:
        return False

def ffprobe_available():
    if shutil.which("ffprobe"):
        return True
    else:
        return False
    
def ffmpeg_available():
    if shutil.which("ffmpeg"):
        return True
    else:
        return False
    
def nwjs_available():
    if shutil.which("nw"):
        return True
    else:
        return False

def select_folder(folder_type: str) -> Path:
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_folder = Path(filedialog.askdirectory(title=f"Selecciona la carpeta de {folder_type} o cancela para omitir"))
    tk_root.destroy()
    return selected_folder
    
def audio_processing_allowed(project_folder:Path) -> bool:
    if ffprobe_available() and ffmpeg_available() and project_folder != Path():
        return True
    else:
        return False
    
def image_processing_allowed(project_folder:Path) -> bool:
    if cwebp_available() and project_folder != Path():
        return True
    else:
        return False

def nwjs_processing_allowed(project_folder:Path):
    if nwjs_available() and project_folder != Path():
        return True
    else:
        return False

def get_folder_size(folder:Path) -> float:
    size = sum(file.stat().st_size for file in folder.rglob('*') if file.is_file())
    size = round(size/1000000, ndigits=2)
    return size

def get_script_folder() -> Path:
    return Path(__file__).parent

def get_logs_folder() -> Path:
    logs_folder = get_script_folder()/"logs"
    if not logs_folder.exists():
        logs_folder.mkdir(parents=True, exist_ok=True)
    return logs_folder

def get_game_launch_file() -> Path:
    return get_script_folder()/"nwjs_game_launch.bat"

def get_compressed_folder() -> Path:
    compressed_folder = get_script_folder()/"compressed"
    if not compressed_folder.exists():
        compressed_folder.mkdir(parents=True, exist_ok=True)
    return compressed_folder

def cpu_threads() -> int:
    cpu_cores = os.cpu_count()
    if cpu_cores is None:
        # No se pudo detectar, por defecto solo usamos 1 hilo
        return 1
    else:
        # La cantidad de hilos de procesamiento serán la cantidad de nucleos - 1
        return max(1, cpu_cores -1)

def set_cpu_threads() ->int:
    print(f"Se recomienda mantener los procesos simultáneos por debajo de: {os.cpu_count()}")
    process_quantity = input("Ingresa la cantidad de procesos simultanes deseados: ")
    try:
        process_quantity = int(process_quantity)
        return process_quantity
    except ValueError:
        print("Error, no se introdujo un valor válido")
        print("Se asignará 1 solo procesos simultáneo")
        return 1
    # end try

def default_image_profile_name() -> str:
    return "PERFORMANCE"

def default_cwebp_flags() -> list[str]:
    return ["cwebp", "-q", "80", "-alpha_q", "100", "-exact", "-f", "30", "-af", "-quiet"]

def audio_extensions() -> tuple[str,...]:
    return (".ogg", ".mp3", ".wav", ".m4a", ".flac")

def image_extensions() -> tuple[str,...]:
    return (".jpg", ".jpeg", ".webp", ".png")

def useless_extensions() -> tuple[str,...]:
    return (".psd",)

def encrypted_extensions() -> tuple[str,...]:
    return (".rpgmvp", ".rpgmvm", ".rpgmvo",   # RPGM MV
            ".rpgmzp", ".rpgmzm", ".rpgmzo",   # RPGM MZ
            "ogg_", "m4a_", "wav_", "mp3_",    # Otros posibles archivos de audio cifrados
            "jpg_", "jpeg_", "png_", "webp_")  # Otros posibles archivos de imagen cifrados

def nwjs_files() -> tuple[str,...]:
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

def nwjs_folders() -> tuple[str,...]:
    return ("locales", "swiftshader")

def delete_folder_content(folder:Path) -> float:
    folder_size:float = 0.0
    for root, dirs, files in folder.walk():
        for file in files:
            file_path = (root/file)
            if file_path.exists():
                try:
                    folder_size += file_path.stat().st_size
                    file_path.unlink()
                    print(f"Eliminado: {file} de: {root.relative_to(Path(folder).parent)}")
                except PermissionError:
                    if file_path.exists():
                        command_delete_cmd = [
                            "cmd", "/c", "del", "/f", "/q", f"{file_path}"
                        ]
                        subprocess.run(command_delete_cmd, shell=True)
                    print(f"(CMD) Eliminado: {file} de: {root.relative_to(Path(folder).parent)}")
                except subprocess.CalledProcessError as e:
                    log_exception(e, "delete_folder_content", "subprocess cmd error", file_path)
                except Exception as e:
                    log_exception(e, "delete_folder_content", "file deletion error", file_path)
    for root, dirs, files in folder.walk(top_down=False):
        for dir in dirs:
            if (root/dir).exists():
                try:
                    (root/dir).rmdir()
                    print(f"Eliminado: {dir} de: {root.relative_to(Path(folder).parent)}")
                except Exception as e:
                    log_exception(e, "delete_folder_content", "folder deletion error", (root/dir))
                # end try
    return folder_size

def delete_compressed_folder_content():
    compressed_folder = get_compressed_folder()
    for root, dirs, files in compressed_folder.walk():
        for file in files:
            try:
                (root/file).unlink()
            except Exception as e:
                log_exception(e, "delete_compressed_folder_content", "file deletion", Path(root/file).parent)
    for root, dirs, files in compressed_folder.walk(top_down=False):
        for dir in dirs:
            try:
                (root/dir).rmdir()
            except Exception as e:
                log_exception(e, "delete_compressed_folder_content", "dir deletion", Path(root/dir))

def delete_files_in_list(folder: Path, files_to_remove: tuple[str,...]) -> float:
    files_size:float = 0.0
    for root, _, files in folder.walk():
        for file in files:
            if file in files_to_remove:
                file_path = Path(root/file)
                if file_path.exists():
                    try:
                        files_size += file_path.stat().st_size
                        file_path.unlink()
                        print(f"Eliminado: {file} de: {file_path.parent.relative_to(Path(folder).parent)}")
                    except Exception as e:
                        log_exception(e, "delete_files_in_list", "file deletion", file_path)
    return files_size

def delete_folders_in_list(folder: Path, folders_to_remove: tuple[str,...]) -> float:
    folder_size:float = 0.0
    for root, dirs, _ in folder.walk():
        for dir in dirs:
            if dir in folders_to_remove:
                if (root/dir).exists():
                    try:
                        folder_size += delete_folder_content(root/dir)
                        folder_parent = (root/dir).parent
                        (root/dir).rmdir()
                        print(f"Eliminado: {dir} de: {folder_parent.relative_to(folder.parent)}")
                    except Exception as e:
                        log_exception(e, "delete_folders_in_list", "folder deletion", (root/dir))
    return folder_size

def get_appdata() -> Path:
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata == None:
        return Path()
    return Path(local_appdata)

def setup_nwjs_game_launcher(project_folder: Path):
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata == None:
        print("Selecciona la carpeta Local que está dentro de AppData")
        print("Usualmente en: C:/Users/(tu usuario)/AppData/Local")
        local_appdata = select_folder("Local AppData")
        if local_appdata == Path():
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

def clear_logs(project_folder:Path):
    project_logs_path = get_logs_folder()/project_folder
    if project_logs_path.exists():
        delete_folder_content(project_logs_path)

def get_audio_hz(project_folder:Path, file: Path) -> int:
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
        file_log(project_folder, "log_hz_error", file)
    # end try
    return hz

def create_subfolders_structure(file_pairs:list[tuple[Path,Path]]):
    for _, compressed in file_pairs:
        compressed_parent = compressed.parent
        if not compressed_parent.exists():
            compressed_parent.mkdir(parents=True, exist_ok=True)


def create_file_pairs_list(project_folder:Path, extensions:tuple[str,...], suffix:str) -> list[tuple[Path,Path]]:
    file_pairs:list[tuple[Path,Path]] = []
    for root, _, files in project_folder.walk():
        for file in files:
            if file.lower().endswith(extensions):
                source_file = root/file
                rel_source_file = source_file.relative_to(project_folder)
                output_file = get_compressed_folder()/rel_source_file.with_suffix(suffix)
                file_pairs.append((source_file, output_file))
    return file_pairs
   
def filter_audio_pairs(project_folder:Path, audio_list:list[tuple[Path,Path]]) -> list[tuple[Path,Path,int]]:
    filtered_list:list[tuple[Path,Path,int]] = []
    for file_pairs in audio_list:
        source, output = file_pairs
        source_hz = get_audio_hz(project_folder, source)
        if source_hz >= 22050:
            if source_hz < 32000:
                target_hz = 22050
            else:
                target_hz = 32000
            filtered_list.append((source, output, target_hz))
    return filtered_list

def compress_audio(source_output_hz:tuple[Path, Path, int]):
    source, output, hz = source_output_hz
    command_ffmpeg = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error",
                    "-i", f"{source}",
                    "-c:a", "libvorbis", 
                    "-ar", f"{hz}", 
                    "-q:a", "0", 
                    "-y", f"{output}"
                ]
    if source.exists():
        try:
            print(f"Procesando: {output}")
            subprocess.run(command_ffmpeg)
        except Exception as e:
            log_exception(e, "compress_audio", "subprocess error", output)
    # end try
    
def process_audio(project_folder:Path) -> list[tuple[Path, Path, int]]:
    extensions:tuple[str,...] = audio_extensions()
    max_threads:int = cpu_threads()
    list_source_output = create_file_pairs_list(project_folder, extensions, suffix=".ogg")
    create_subfolders_structure(list_source_output)
    list_source_output_hz = filter_audio_pairs(project_folder, list_source_output)
    if len(list_source_output_hz) > 0:
        with ThreadPoolExecutor(max_threads) as executor:
            executor.map(compress_audio, list_source_output_hz)
    return list_source_output_hz

def compress_image(cwebp_flags:list[str], source_output_pair:tuple[Path,Path]):
    source, output = source_output_pair
    command_cwebp = cwebp_flags.copy()
    command_cwebp.append(f"{source}")
    command_cwebp.append("-o")
    command_cwebp.append(f"{output}")
    if len(command_cwebp) > 0 and source.exists():
        try:
            print(f"Procesando: {output}")
            subprocess.run(command_cwebp)
        except Exception as e:
            log_exception(e, "compress_image", "subprocess error", output)
        # end try

def process_images(project_folder:Path, cwebp_flags:list[str]):
    extensions:tuple[str,...] = image_extensions()
    max_threads:int = cpu_threads()
    list_source_output = create_file_pairs_list(project_folder, extensions, suffix=".webp")
    create_subfolders_structure(list_source_output)
    if len(list_source_output) > 0:
        with ThreadPoolExecutor(max_threads) as executor:
            executor.map(
            partial(compress_image, cwebp_flags),    # Función compress_image con argumento adicional cwebp_flags
            list_source_output                       # Iterable para executor
            )
    return list_source_output

def log_processed_files(project_folder:Path, list:list[tuple[Path,Path]], log_name:str):
    for original, compressed in list:
        original_size = original.stat().st_size
        original_size = round(original_size/1000, ndigits=2)

        compressed_size = compressed.stat().st_size
        compressed_size = round(compressed_size/1000, ndigits=2)

        relative_paths = original.relative_to(project_folder)
        with open(f"{get_logs_folder()/log_name}.log", "a") as f:
            f.write(f"{relative_paths.parents} \n    {original.name} {original_size}KB -> {compressed_size}KB\n")

def replace_file(project_folder:Path, original_file:Path, compressed_file:Path, cumulative_size_total:float, cumulative_size_saved:float) -> tuple[float,float]:
    if compressed_file.exists():
        original_file_size = original_file.stat().st_size
        cumulative_size_total += original_file_size
        compressed_file_size = compressed_file.stat().st_size
        if 0 < compressed_file_size < original_file_size:
            try:
                shutil.move(compressed_file, original_file)
                cumulative_size_saved += original_file_size - compressed_file_size
                print(f"Reemplazando {original_file.relative_to(project_folder)}")
                file_log(project_folder, "Original_replaced", compressed_file)
            except Exception as e:
                log_exception(e, "repalce_originals", "shutil move error", compressed_file)
            # end try
        else:
            compressed_file.unlink()
            print(f"NO Reemplazando {original_file.relative_to(project_folder)}")
            print(f"   Archivo comprimido: {original_file.relative_to(project_folder)} resulto ser más grande que el original")
            file_log(project_folder, "Compressed_deleted", compressed_file)
    return cumulative_size_total, cumulative_size_saved

def repalce_originals_img(project_folder:Path, file_pairs:list[tuple[Path,Path]]) -> tuple[float, float]:
    cumulative_size_total:float = 0.0
    cumulative_size_saved:float = 0.0
    for original_file, compressed_file in file_pairs:
        cumulative_size_total, cumulative_size_saved = replace_file(project_folder, original_file, compressed_file, cumulative_size_total, cumulative_size_saved)
    return cumulative_size_total, cumulative_size_saved

def repalce_originals_aud(project_folder:Path, files_list:list[tuple[Path,Path,int]]) -> tuple[float, float]:
    cumulative_size_total:float = 0.0
    cumulative_size_saved:float = 0.0
    for original_file, compressed_file, _ in files_list:
        cumulative_size_total, cumulative_size_saved = replace_file(project_folder, original_file, compressed_file, cumulative_size_total, cumulative_size_saved)
    return cumulative_size_total, cumulative_size_saved

def post_compress_info(original_size:float, saved_size:float):
    # Mostrar espacio en disco ahorrado
    print(f"Tamaño de archivos de medios originales: {round(original_size/1000000, ndigits=2)}MB")
    print(f"Tamaño de archivos de medios comprimidos: {round((original_size-saved_size)/1000000, ndigits=2)}MB")
    print(f"Al reemplazar los originales se ha ahorrado en total: {round(saved_size/1000000, ndigits=2)}MB")


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

def main_menu(project_folder:Path = Path()):
    image_profile_name:str = default_image_profile_name()
    cwebp_flags:list[str] = default_cwebp_flags()
    project_size:float = 0.0
    if project_folder != Path():
        project_size = get_folder_size(project_folder)
    project_processed:bool = False
    while True:
        print("="*50)
        print("     MENU PRINCIPAL")
        print("="*50)

        if project_folder != Path(): 
            print(f"Tamaño inicial del proyecto: {project_size}MB", \
                  f"\nTamaño Actual del proyecto: {get_folder_size(project_folder)}MB" if project_processed else "")

        options_range:list[int] = [0,1,2]
        print(f"1 - Seleccionar ruta del proyecto. Actual:", f"{project_folder}" if project_folder != Path() else "NO SELECCIONADA")
        print(f"2 - Menu opciones de calidad de conversión de imágenes. Preset Actual: {image_profile_name}")
        
        if project_folder != Path():
            if image_processing_allowed(project_folder):
                print(f"3 - Iniciar compresión de Imágenes")
                options_range.append(3)
            else: print(f"3 - [X] Compresión de Imágenes no disponible sin cwebp")
            if audio_processing_allowed(project_folder):
                print(f"4 - Iniciar compresión de audio")
                options_range.append(4)
            else: print(f"4 - [X] Compresión de audio no disponible sin ffmpeg y ffprobe")
            if image_processing_allowed(project_folder) and audio_processing_allowed(project_folder):
                print(f"5 - Iniciar compresión de imágenes y audio")
                options_range.append(5)
            else: print(f"5 - [X] Compresión de imágenes y audio no disponible sin apps correspondientes")
            if get_game_launch_file().exists() and nwjs_processing_allowed(project_folder):
                print(f"6 - Instalar y configurar {get_game_launch_file().name}")
                options_range.append(6)
            else: print(f"6 - [X] No se puede Instalar y configurar {get_game_launch_file().name} si el archivo no existe junto a este script")
            print(f"7 - Limpiar NW.js local del directorio del proyecto")
            options_range.append(7)
        print("8 - Borrar logs")
        options_range.append(8)
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
                    old_project_folder = project_folder
                    project_folder = select_folder("Proyecto")
                    if old_project_folder != project_folder:
                        delete_compressed_folder_content()
                        project_size = get_folder_size(project_folder)
                        project_processed = False
                elif option_main == 2:
                    image_profile_name, cwebp_flags = menu_image_profile(image_profile_name, cwebp_flags)
                elif option_main == 3:
                    print("Ejecutando tarea de compresión de imágenes...")
                    image_path_pairs = process_images(project_folder, cwebp_flags)
                    cumulative_size_total, cumulative_size_saved = repalce_originals_img(project_folder, image_path_pairs)
                    post_compress_info(cumulative_size_total, cumulative_size_saved)
                    project_processed = True
                    input("\nTarea Finalizada. Presiona Enter para continuar")
                elif option_main == 4:
                    print("Ejecutando tarea de compresión de audio...")
                    audio_path_pairs = process_audio(project_folder)
                    cumulative_size_total, cumulative_size_saved = repalce_originals_aud(project_folder, audio_path_pairs)
                    post_compress_info(cumulative_size_total, cumulative_size_saved)
                    project_processed = True
                    input("\nTarea Finalizada. Presiona Enter para continuar")
                elif option_main == 5:
                    print("Ejecutando tarea de compresión de imágenes y audio...")
                    image_path_pairs = process_images(project_folder, cwebp_flags)
                    audio_path_pairs_hz = process_audio(project_folder)
                    repalce_originals_img(project_folder, image_path_pairs)
                    repalce_originals_aud(project_folder, audio_path_pairs_hz)
                    project_processed = True
                    input("\nTarea Finalizada. Presiona Enter para continuar")
                elif option_main == 6:
                    print("Preparando el entorno del juego...")
                    setup_nwjs_game_launcher(project_folder)
                    print("nwjs_game_launch instalado y configurado")
                    subprocess.run(f"{project_folder/get_game_launch_file().name}", cwd=f"{project_folder}")
                    print("Juego lanzado")
                elif option_main == 7:
                    print(f"Borrando archivos de NW.js locales en {project_folder.name}...")
                    delete_files_in_list(project_folder, nwjs_files())
                    delete_folders_in_list(project_folder, nwjs_folders())
                    print(f"Archivos locales de NW.js eliminados de {project_folder.name}")
                    project_processed = True
                elif option_main == 8:
                    print("Borrando logs...")
                    delete_folder_content(get_logs_folder())
            else:
                print(f"Número fuera del rango {str(options_range)}.")

        except ValueError:
            print(f"¡Error! Ingresaste algo que no es un número")
        except Exception as e:
            log_exception(e, "Main Menu")

delete_compressed_folder_content()
main_menu(select_folder("Proyecto"))

print("=============================================")
print("Programa terminado. Presione enter para salir")
input("=============================================")
sys.exit()
