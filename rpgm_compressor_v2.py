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
def log_exception(e:Exception, exception_source:str = "Unknown", msg:str = "None", file:Path = Path()):
    """ Función que se lanza cuando ocurre una excepción.

    Guarda un registro con la función donde ocurrió la excepción y un mensaje dentro de la carpeta logs del programa """

    print(f"Ocurrió un error inesperado en: {exception_source}")
    print(f"Mensaje de error: \n {e}")
    with open(f"{get_logs_folder()}/error_{exception_source}.log", "a") as f:
        if file != Path():
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

def select_folder(folder_type: str) -> Path:
    """ Abre la ventana de dialogo de selección de directorios """
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_folder = Path(filedialog.askdirectory(title=f"Selecciona la carpeta de {folder_type} o cancela para omitir"))
    tk_root.destroy()
    return selected_folder
    
def audio_processing_allowed(project_folder:Path) -> bool:
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a audio """
    if ffprobe_available() and ffmpeg_available() and project_folder != Path():
        return True
    else:
        return False
    
def image_processing_allowed(project_folder:Path) -> bool:
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a imágenes """
    if cwebp_available() and project_folder != Path():
        return True
    else:
        return False

def nwjs_processing_allowed(project_folder:Path):
    """ Devuelve True si se cumplen los requisitos para que el programa ejecute las tareas relacionadas a NW.js """
    if nwjs_available() and project_folder != Path():
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
                        print(f"Eliminado: {file_path.name} de: {file_path.parent.relative_to(folder.parent)}")
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
                        print( f"Eliminado directorio: {current_folder.name} de {current_folder.parent}")
                    except Exception as e:
                        log_exception(e, "delete_folders_in_list", "rmtree in delete_folder", current_folder)
    return folder_size

def get_localappdata() -> Path:
    """ Devuelve un Path con la dirección de la carpeta ~/AppData/Local, y si no la encuentra devuelve un Path vacio """
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata == None:
        return Path()
    return Path(local_appdata)

def setup_nwjs_game_launcher(project_folder: Path):
    """ Realiza la instalación y configuración del launcher personalizado del juego:

     - Crea un directorio para el perfil del juego en una carpeta específica en Local AppData que será la carpeta universal para todos los juegos.

     - Modifica el archivo de configuración json del juego para usar la carpeta creada anteriormente como perfil.

     - Instala el archivo .bat del launcher personalizado dentro de la caerpeta del juego """
    local_appdata = get_localappdata()
    if local_appdata == Path():
        print("Selecciona la carpeta Local que está dentro de AppData")
        print("Usualmente en: C:/Users/(tu usuario)/AppData/Local")
        local_appdata = select_folder("Local AppData")
        if local_appdata == Path() or local_appdata.name != "Local":
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

def compress_file(project_folder:Path, cwebp_flags:list[str], source:Path):
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = get_compressed_folder()/rel_source
        command:list[str] = []
        if source.suffix in get_image_extensions():
            output = output.with_suffix(".webp")
            command = cwebp_flags.copy()
            command.append(f"{source}")
            command.append("-o")
            command.append(f"{output}")

        elif source.suffix in get_audio_extensions():
            output = output.with_suffix(".ogg")
            hz = get_audio_hz(project_folder, source)
            if 22050 <= hz < 32000:
                hz = 22050
            else:
                hz = 32000
            command = [
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
                print("ERROR")

            if output.exists() and source.exists():
                if output.stat().st_size < source.stat().st_size:
                    try:
                        source.unlink()
                        shutil.move(output, source.parent)
                    except Exception as e:
                        # TODO
                        print("ERROR")
                else:
                    try:
                        output.unlink()
                    except Exception as e:
                        # TODO
                        print("ERROR")
# END of function compress_file()

def get_source_list(project_folder:Path, extensions:tuple[str,...]) -> list[Path]:
    source_file_list:list[Path] = []
    for root, _, files in project_folder.walk():
        for file in files:
            if file.lower().endswith(extensions):
                source_file = root/file
                source_file_list.append(source_file)
    return source_file_list

def create_output_path(project_folder:Path, source_file_list:list[Path]):
    for source_file in source_file_list:
        rel_source_file = source_file.relative_to(project_folder)
        output_file = get_compressed_folder()/rel_source_file
        if not output_file.parent.exists():
            output_file.parent.mkdir(parents=True, exist_ok=True)

def process_files(project_folder:Path, extensions:tuple[str,...], cwebp_flags:list[str]):
    max_threads = get_cpu_threads()
    source_list = get_source_list(project_folder, extensions)
    if len(source_list) > 0:
        create_output_path(project_folder, source_list)
        with ThreadPoolExecutor(max_threads) as executor:
            executor.map(
                partial(compress_file, project_folder, cwebp_flags),
                source_list
                )

def compare_project_size(original_size:float, new_size:float):
    # Mostrar espacio en disco ahorrado
    print(f"Tamaño de archivos de medios originales: {original_size}MB")
    print(f"Tamaño de archivos de medios comprimidos: {original_size-new_size}MB")
    print(f"Al reemplazar los originales se ha ahorrado en total: {new_size}MB")

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
    image_profile_name:str = get_default_image_profile_name()
    cwebp_flags:list[str] = get_default_cwebp_flags()
    compressed_folder:Path = get_compressed_folder()
    initial_project_size:float = 0.0
    if project_folder != Path():
        initial_project_size = get_folder_size(project_folder)
    project_processed:bool = False
    while True:
        print("="*50)
        print("     MENU PRINCIPAL")
        print("="*50)

        if project_folder != Path(): 
            print(f"Tamaño inicial del proyecto: {initial_project_size}MB", \
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
                    new_project_folder = select_folder("Proyecto")
                    if new_project_folder != project_folder and new_project_folder != Path():
                        delete_folder_content(compressed_folder)
                        project_folder = new_project_folder
                        initial_project_size = get_folder_size(project_folder)
                        project_processed = False
                elif option_main == 2:
                    image_profile_name, cwebp_flags = menu_image_profile(image_profile_name, cwebp_flags)
                elif option_main == 3:
                    print("Ejecutando tarea de compresión de imágenes...")
                    process_files(project_folder, get_image_extensions(), cwebp_flags)
                    compare_project_size(initial_project_size, get_folder_size(project_folder))
                    delete_folder_content(compressed_folder)
                    project_processed = True
                    input("\nTarea Finalizada. Presiona Enter para continuar")
                elif option_main == 4:
                    print("Ejecutando tarea de compresión de audio...")
                    process_files(project_folder, get_audio_extensions(), cwebp_flags)
                    compare_project_size(initial_project_size, get_folder_size(project_folder))
                    delete_folder_content(compressed_folder)
                    project_processed = True
                    input("\nTarea Finalizada. Presiona Enter para continuar")
                elif option_main == 5:
                    print("Ejecutando tarea de compresión de imágenes y audio...")
                    img_and_aud_extensions = (*get_image_extensions(), *get_audio_extensions())
                    process_files(project_folder, img_and_aud_extensions, cwebp_flags)
                    compare_project_size(initial_project_size, get_folder_size(project_folder))
                    delete_folder_content(compressed_folder)
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
                    delete_files_in_list(project_folder, get_nwjs_files())
                    delete_folders_in_list(project_folder, get_nwjs_folders())
                    print(f"Archivos locales de NW.js eliminados de {project_folder.name}")
                    compare_project_size(initial_project_size, get_folder_size(project_folder))
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


if any(get_compressed_folder().iterdir()):
    delete_folder_content(get_compressed_folder())
main_menu(select_folder("Proyecto"))

print("=============================================")
print("Programa terminado. Presione enter para salir")
input("=============================================")
sys.exit()
