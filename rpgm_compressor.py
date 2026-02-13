import os, sys, subprocess, shutil, json, ctypes
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog
from functools import partial
    
def clear_screen():
    cmd = 'cls' if os.name == 'nt' else 'clear'
    subprocess.run(cmd, shell=True, check=False)
clear_screen()

# Función no utilizada por ahora
""" def require_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        print("Ejecutando con privilegios de administrador")
    else:
        # Re-ejecutar el script con derechos de administrador
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{__file__}"', None, 1
        )
        sys.exit() """
# END of function require_admin()

def check_environment() -> tuple[bool, bool, bool]:
    # Comprobar cwebp en variables de entorno para procesamiento de imágenes
    if shutil.which("cwebp") is None:
        cwebp_available = False
    else:
        cwebp_available = True

    # Comprobar ffmpeg y ffprobe en variables de entorno para procesamiento de audio
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        ffapps_available = False
    else:
        ffapps_available = True

    # Comprobar NW.js en variables de entorno para lanzamiento del juego
    if shutil.which("nw") is None:
        nwjs_available = False
    else:
        nwjs_available = True
    
    if not cwebp_available and not ffapps_available and not nwjs_available:
        print("[X] No se encuentran variables de entorno requeridas")
        print("[X] El programa no puede continuar")
        input("Presione Enter para salir...")
        sys.exit()
    return cwebp_available, ffapps_available, nwjs_available


def folder_selection(folder_type: str) -> Path:
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_folder = Path(filedialog.askdirectory(title=f"Selecciona la carpeta de {folder_type} o cancela para omitir"))
    tk_root.destroy()
    return selected_folder

def subfolder_of(subfolder:Path, parent_folder:Path):
    relative_subfolder = subfolder.relative_to(parent_folder)
    if (parent_folder/relative_subfolder).exists() and parent_folder != parent_folder/relative_subfolder:
        return True
    else:
        return False
        
def select_default_folders(project_folder:Path = Path(), audio_folder:Path = Path(), image_folder:Path = Path()) -> tuple[Path, Path, Path]:
    # OBLIGATORIO Seleccionar carpeta de proyecto
    temp_project_folder = folder_selection("Proyecto")
    if temp_project_folder == Path():
        print("[X] No se ha seleccionado carpeta de proyecto")
        # Si cancelamos, las varaibles no se actualizan
        return project_folder, audio_folder, image_folder
    
    project_folder = temp_project_folder
    # Detección de ruta de audio
    if Path(project_folder/"audio").exists():
        audio_folder = project_folder / "audio"
    elif Path(project_folder/"www/audio").exists():
        audio_folder = project_folder / "www/audio"
    else:
        audio_folder = folder_selection("Audio")  # Forzar selección manual si no se detectan carpetas predeterminadas
        if not subfolder_of(audio_folder, project_folder):
            audio_folder = Path()

    # Detección de ruta de imágenes
    if Path(project_folder/"img").exists():
        image_folder = project_folder / "img"
    elif Path(project_folder/"www/img").exists():
        image_folder = project_folder / "www/img"
    else:
        image_folder = folder_selection("Imagenes")  # Forzar selección manual si no se detectan carpetas predeterminadas
        if not subfolder_of(image_folder, project_folder):
            image_folder = Path()

    # Return devuelve rutas correctas o Path()
    return project_folder, audio_folder, image_folder
# END of function check_folders()


def audio_processing_allowed() -> bool:
    if ffapps_available and subfolder_of(audio_folder, project_folder):
        return True
    else:
        return False

def image_processing_allowed() -> bool:
    if cwebp_available and subfolder_of(image_folder, project_folder):
        return True
    else:
        return False
# END of function check_allowed_functions()

def set_output_folder(project_folder:Path, subfolder:Path) -> Path:
    compressed_folder = Path(__file__).parent / "compressed"
    media_output = compressed_folder / subfolder.relative_to(project_folder)
    # Crear carpetas de salida si no existen
    media_output.mkdir(parents=True, exist_ok=True)
    return media_output
# END of function set_output_folder()

# Cantidad de procesos máximos para compresión de medios
def set_cpu_threads() -> int:
    cpu_cores = os.cpu_count()
    if cpu_cores is None:
        max_threads = 2
        print("[!] No se pudo detectar la cantidad de núcleos de CPU, se asignarán 2 procesos simultáneos para la compresión")
    else:
        # Usamos un máximo de núcleos disponibles menos uno, con un límite de 6 para evitar saturar el sistema
        max_threads = max(1, min(cpu_cores - 1, 6))
    print(f"[+] Procesos de converión simultáneos: {max_threads}")
    return max_threads
# END of function set_cpu_threads()

# Perfil de compresión de imágenes predeterminado (puede ser cambiado en el menú principal)
def default_image_profile() -> tuple[str, list[str]]:
    image_profile_name :str= "PERFORMANCE"
    cwebp_flags :list = ['cwebp', "-q", "80", '-alpha_q', '100', '-exact', '-f', '30', '-af', "-quiet"]
    return image_profile_name, cwebp_flags
# END of function default_image_profile()


def detection_filters():
    audio_ext = (".ogg", ".mp3", ".wav", ".m4a", ".flac")
    image_ext = (".jpg", ".jpeg", ".webp", ".png")
    useless_ext = (".psd")
    encrypted_ext = (".rpgmvp", ".rpgmvm", ".rpgmvo",  # RPGM MV
                    ".rpgmzp", ".rpgmzm", ".rpgmzo",   # RPGM MZ
                    "ogg_", "m4a_", "wav_", "mp3_",    # Otros posibles archivos de audio cifrados
                    "jpg_", "jpeg_", "png_", "webp_")  # Otros posibles archivos de imagen cifrados

    
    
    
    
    
    
    nwjs_files = ("credits.html", "d3dcompiler_47.dll",
                "ffmpeg.dll", "icudtl.dat", 
                "libEGL.dll", "libGLESv2.dll", 
                "node.dll", "nw.dll",
                "nw_100_percent.pak", "nw_200_percent.pak", 
                "nw_elf.dll", "resources.pak", 
                "debug.log", "natives_blob.bin", 
                "snapshot_blob.bin", "v8_context_snapshot.bin",
                "notification_helper.exe", "vulkan-1.dll",
                "vk_swiftshader_icd.json", "vk_swiftshader.dll")
    nwjs_folders = ("locales", "swiftshader")
    return audio_ext, image_ext, useless_ext, encrypted_ext, nwjs_files, nwjs_folders
# END of function detection_filters()

def remove_folder_contents(folder: Path):
    for root, dirs, files in folder.walk():
        for file in files:
            file_path = (root/file)
            try:
                file_path.unlink()
                print(f"Eliminado: {file} de: {root.relative_to(Path(folder).parent)}")
            except PermissionError:
                if file_path.exists():
                    command_delete_cmd = [
                        "cmd", "/c", "del", "/f", "/q", f"{file_path}"
                    ]
                    result = subprocess.run(command_delete_cmd, shell=True)
                print(f"(CMD) Eliminado: {file} de: {root.relative_to(Path(folder).parent)}")
            except subprocess.CalledProcessError as e:
                print(f"[X] No se eliminó {file} con comando del.")
                print(f"  Comprobar manualmente: {(file_path).parent}")
            except Exception as e:
                print(f"[X] No se eliminó {file}. Comprobar manualmente: {(file_path).parent}")
                print(f"  Detalles del error: {e}")
        # end for files
    # end for walk
# END of function remove_folder_contents()

# Eliminar todos los archivos de subcarpetas, una vez las carpetas están vacias eliminar la carpeta misma
def delete_tree_folder(folder: Path):
    for root, dirs, files in folder.walk(top_down=False):
        for file in files:
            try:
                (root/file).unlink()
                print(f"Eliminado: {file} de: {root.relative_to(Path(folder).parent)}")
            except:
                print(f"No se eliminó {file}. Comprobar manualmente: {(root/file).parent}")
        # end for files
        for dir in dirs:
            try:
                (root/dir).rmdir()
                print(f"Eliminada carpeta vacía: {(root/dir).relative_to(Path(folder).parent)}")
            except:
                print(f"No se eliminó la carpeta vacía {dir}. Comprobar manualmente: {(root/dir).parent}")
        # end for dirs
    # end for walk
    folder.rmdir()
    print(f"Eliminada carpeta: {folder.relative_to(Path(folder).parent)}")
# END of function delete_tree_folder()

def remove_files_from_list(folder: Path, files_to_remove: tuple):
    for root, dirs, files in folder.walk():
        for file in files:
            if file in files_to_remove:
                file_path = Path(root/file)
                file_parent = file_path.parent
                try:
                    file_path.unlink()
                    print(f"Eliminado: {file} de: {file_parent.relative_to(Path(folder).parent)}")
                except:
                    print(f"No se eliminó {file}. Comprobar manualmente: {file_path.parent}")
                # end try
    # end for walk
# END of function remove_files_from_list()

""" Old launch method using subprocess directly, now replaced by nwjs_game_launch.bat for better compatibility"""
"""
def launch_nwjs_game(project_folder: Path):
    nwjs_command = [
        "nw", 
        f"--user-data-dir={rpgm_user_profile}", 
        "--nwapp", 
        str(project_folder)
    ] 
    try:
        subprocess.Popen(nwjs_command,
                         cwd=str(project_folder) 
                         #creationflags=subprocess.CREATE_NEW_CONSOLE,
                         #shell=True
                         )
    except Exception as e:
        print(f"Error al lanzar el juego: {e}")
# END of funtion launch_nwjs_game()
"""

def setup_nwjs_game_launcher(project_folder: Path):
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata == None:
        input("Ocurrió un error al detectar directorio de AppData en el sistema")
        return
    try:
        local_appdata = Path(local_appdata)
    except:
        input("Ocurrió un error al detectar directorio de AppData en el sistema")
        return
    rpgm_user_profile = Path(local_appdata)/"RPGM/User Data"

    # Borrar todos los archivos en rpgm_user_profile
    if rpgm_user_profile.exists():
        remove_folder_contents(rpgm_user_profile)

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
        print(f"¡JSON está mal formado! Error en la línea {e.lineno}, columna {e.colno}")
        input(f"Mensaje del error: {e.msg}")
    except Exception as e:
        input(f"Ocurrió algo raro: {e}")
    # Update package.json END

    nwjs_game_launcher = Path(__file__).parent / "nwjs_game_launch.bat"
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
            print(f"[X] Error al copiar el script de NWJS Game Launcher: {e}")
# END of function install_nwjs_game_launch()

# Función toma una lista de tuplas de archivos de audio (source, output)
# y decide si procesar o no cada archivo de audio
def compress_audio(paths: list):
    source, output = paths
    # Verificamos los Hz de un archivo source
    command_probe = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        f"{source}"
    ]
    try:
        result = subprocess.run(command_probe, capture_output=True, text=True)
        hz =int(result.stdout.strip())
    except:
        # Si hay errores al obtener los Hz...
        hz = 0
        print(f"[-] Ignorando (posible corrupción de archivo con {hz}Hz): {source.name}")
        return
    # Si los Hz son menores a 32000 omitimos el procesamiento del archivo
    
    # Selección de flags de ffmpeg según los Hz del archivo original
    if 22000 <= hz < 32000:
        # Configuración para archivos de 22kHz con calidad 0
        command_mpeg = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error",
                    "-i", f"{source}",
                    "-c:a", "libvorbis", 
                    "-ar", "22050", 
                    "-q:a", "0", 
                    "-y", f"{output}"
                ]
        compressed_hz = 22050
    elif hz >= 32000:
        # Configuración para archivos de 32kHz con calidad 0
        command_mpeg = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error",
                    "-i", f"{source}",
                    "-c:a", "libvorbis", 
                    "-ar", "32000", 
                    "-q:a", "0", 
                    "-y", f"{output}"
                ]
        compressed_hz = 32000
    else:
        print(f"[-] Ignorando (Hz no soportados: {hz}Hz): {source.name}")
        return
    
    # Si el archivo tiene Hz válidos, se procesa con la configuración seleccionada
    print(f"Comprimiendo {hz}Hz -> {compressed_hz}Hz: {source.name}")
    try:
        subprocess.run(command_mpeg) 
    except:
        print("[X] Error en comando mpeg")
    # END Try
# END of function compress_audio()

def process_audio(audio_folder: Path, audio_ext: tuple, audio_output: Path, max_threads: int):
    print("----Procesando Audio----")
    audio_output.mkdir(parents=True, exist_ok=True)
    audio_files_pairs = []
    for root, dirs, files in audio_folder.walk():
        for file in files:
            if file.lower().endswith(audio_ext):
                source_file = Path(root) / file
                output_file = (audio_output / source_file.relative_to(audio_folder)).with_suffix(".ogg")    # Forzamos extensión .ogg
                output_file.parent.mkdir(parents=True, exist_ok=True)
                audio_files_pairs.append((source_file, output_file))
            # END IF
        # END FOR files
    # END FOR walk
    # iniciamos el procesamiento de audio en paralelo
    with ThreadPoolExecutor(max_threads) as executor:
        executor.map(compress_audio, audio_files_pairs)
# END of audio processing block

def compress_image(cwebp_flags: list, paths: list):
    source, output = paths
    command_cwebp = cwebp_flags.copy()
    # cwebp_flags ya incluye el comando 'cwebp' al inicio, por lo que solo agregamos los argumentos específicos del archivo
    command_cwebp.append(f"{source}")
    command_cwebp.append("-o")
    command_cwebp.append(f"{output}")

    # Si el comando cwebp tiene más de un elemento (es decir, si se ha configurado correctamente), lo ejecutamos
    if len(command_cwebp) > 0:
        print(f"Comprimiendo imagen: {source.name}")
        try:
            subprocess.run(command_cwebp)
        except:
            print("[X] Error en comando cwebp")
        # END TRY
    # END IF len comando
# END of function compress_image()

def process_images(image_folder: Path, image_ext: tuple, image_output: Path, max_threads: int, cwebp_flags: list):
    print("---Procesando Imágenes---")
    image_output.mkdir(parents=True, exist_ok=True)
    image_files_pairs = []
    for root, dirs, files in image_folder.walk():
        for file in files:
            if file.lower().endswith(image_ext):
                source_file = Path(root) / file
                output_file = image_output / source_file.relative_to(image_folder)    # Sin cambiar extensión para evitar problemas del RPGM engine
                output_file.parent.mkdir(parents=True, exist_ok=True)
                image_files_pairs.append((source_file, output_file))
            # END IF
        # END FOR files
    # END FOR walk
    # iniciamos el procesamiento de imágenes en paralelo
    with ThreadPoolExecutor(max_threads) as executor:
        executor.map(
            partial(compress_image, cwebp_flags),   # Función compress_image con argumento adicional cwebp_flags
            image_files_pairs                       # Iterable para executor
            )
# END of image processing block

def replace_originals(proyect_folder: Path, compressed_folder: Path):
    cumulative_size_saved :int = 0
    cumulative_size_total :int = 0
    for root, dirs, files in compressed_folder.walk():
        for file in files:
            compressed_file = Path(root) / file
            compressed_file_size = compressed_file.stat().st_size
            original_file = proyect_folder / compressed_file.relative_to(compressed_folder)
            original_file_size = original_file.stat().st_size
            cumulative_size_total += original_file_size
            if original_file.exists():
                # Solo reemplazamos el archivo original si el comprimido es más pequeño que el original
                # y si el archivo comprimido no está vacío (corrupto)
                if 0 < compressed_file.stat().st_size < original_file.stat().st_size:
                    print(f"[+] Reemplazando {file}")
                    print(f"   Ahorrado: {round((original_file_size - compressed_file_size)/1000, ndigits=2)}KB")
                    shutil.move(f"{compressed_file}", f"{original_file}")
                    cumulative_size_saved += original_file_size - compressed_file_size
                else:
                    # Eliminar el archivo de salida si no es más pequeño o está corrupto
                    print(f"[!] {file} en la carpeta de comprimidos resulto ser más grande. Eliminando...")
                    compressed_file.unlink()
            else:
                # Mover el nuevo archivo si el original no existe (no debería no existir, pero por si acaso)
                print(f"[!] {file} en la carpeta de comprimidos no se encontró en la carpeta original")
                # Mejor no borramos y que el usuario lo verifiqué manualmente después
                # No borrarlo provocará que la carpeta de comprimidos no pueda ser borrada al finalizar esta función
                # shutil.move(str(compressed_file), str(original_file))
            # END if file exist
        # END FOR files
    # END FOR walk
    try:
        # Intentamos borrar la carpeta de comprimidos
        # Si ocurrió un error en el bloque anterior no se borrará
        for root, dirs, files in compressed_folder.walk(top_down=False):
            for dir in dirs:
                (root/dir).rmdir()
    except OSError as e:
        # La carpeta no está vacía, no se puede eliminar
        print(f"[X] No se pudo eliminar {compressed_folder} porque no está vacio")
        print(f"[!] Verifica los archivos en las siguientes carpetas manualmente:")
        print(f"     {compressed_folder}")
        print(f"Detalles del error: {e}")
    
    # Mostrar espacio en disco ahorrado
    print(f"Tamaño de archivos de medios originales: {round(cumulative_size_total/1000000, 2)}MB")
    print(f"Tamaño de archivos de medios comprimidos: {round((cumulative_size_total-cumulative_size_saved)/1000000, 2)}MB")
    print(f"Al reemplazar los originales se ha ahorrado en total: {round(cumulative_size_saved/1000000, 2)}MB")
# END function replace_originals()


def menu_select_project_folder(project_folder:Path, audio_folder:Path, image_folder:Path):
    while True:
        print("")
        print("\n" + "="*50)
        print("     SELECCIÓN DE RUTA DEL PROYECTO")
        print("="*50)

        print("1 - Seleccionar carpeta del proyecto, audio, e imágenes")
        print(f"Carpeta del proyecto actual:\n" \
              f"    {project_folder if not project_folder == Path() else "Ruta Inválida"}")
        print("2 - Seleccionar carpeta de audio")
        print(f"Carpeta de Audio actual:\n" \
              f"    {audio_folder if not audio_folder == Path() else "Ruta Inválida"}")
        print("3 - Seleccionar carpeta de imágenes")
        print(f"Carpeta de Imágenes actual:\n" \
              f"    {image_folder if not image_folder == Path() else "Ruta Inválida"}")
        print("="*50)

        try:
            option_folder = input("Elige una opción (1-3) o 0 para volver al menú principal: ").strip()
            option_folder = int(option_folder)
            if option_folder in [1,2,3,0]:
                if option_folder == 0:
                    if project_folder != Path():
                        return project_folder, audio_folder, image_folder
                elif option_folder == 1:
                    project_folder, audio_folder, image_folder = select_default_folders(project_folder, audio_folder, image_folder)
                elif option_folder == 2:
                    temp_audio_folder = folder_selection("Audio")
                    if subfolder_of(temp_audio_folder, project_folder):
                        audio_folder = temp_audio_folder
                    else:
                        print(f"[!] Ruta de Audio no se encuentra dentro de {project_folder}")
                        audio_folder = Path()
                elif option_folder == 3:
                    temp_image_folder = folder_selection("Image")
                    if subfolder_of(temp_image_folder, project_folder):
                        image_folder = temp_image_folder
                    else:
                        print(f"[!] Ruta de Imagenes no se encuentra dentro de {project_folder}")
                        image_folder = Path()
            else:
                print("Por favor, elige un número entre 0 y 3.")
        except ValueError as e:
            print("Entrada inválida. Ingresa un número.")
        # end try

        

def menu_chose_image_profile(image_profile_name: str, cwebp_flags: list[str]) -> tuple[str, list[str]]:
    cwebp_profiles = {  # indice del perfil : (nombre del perfil, lista de flags para cwebp)
        1: ("PERFORMANCE", ['cwebp', '-q', '80', '-alpha_q', '100', '-exact', '-f', '30', '-af', '-quiet']),
        2: ("MEDIUM", ['cwebp', '-near_lossless', '75', '-alpha_q', '100', '-exact', '-m', '6', '-mt', '-quiet']),
        3: ("QUALITY", ['cwebp', '-lossless', '-z', '9', '-alpha_q', '100', '-exact', '-mt', '-quiet'])
    }
    while True:
        print("")
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
                print("")
                return image_profile_name, cwebp_flags
            else:
                print("Por favor, elige un número entre 0 y 3.")
        except ValueError:
            print("Entrada inválida. Ingresa un número.")
# END of function chose_image_profile

######################
# Variables globales #
######################


""" # Solo de ser necesario
require_admin() """
cwebp_available, ffapps_available, nwjs_available = check_environment()
project_folder, audio_folder, image_folder = select_default_folders()
image_profile_name, cwebp_flags = default_image_profile()
max_threads = set_cpu_threads()
audio_ext, image_ext, useless_ext, encrypted_ext, nwjs_files, nwjs_folders = detection_filters()


if cwebp_available: print("cwebp encontrado. Procesamiento de imágenes disponible")
else: 
    print("[!] No se encontró cwebp en el sistema")
    print("[!] La compresión de imágenes no estará disponible")
if ffapps_available: print("ffmpeg y ffprobe encontrados. Procesamiento de audio disponible")
else:
    print("[!] No se encontró ffmpeg o ffprobe en el sistema")
    print("[!] La compresión de audio no estará disponible")
if nwjs_available: print("nwjs encontrado. instalación de game launcher disponible")
else:
    print("[!] No se encontró NW.js en el sistema")
    print("[!] Lanzar el juego con NW.js del sistema no estará disponible")
    print("[!] Para usar NW.js del sistema, por favor descarga NW.js desde https://nwjs.io/ " \
    "y asegúrate de que el ejecutable 'nw' esté en tu PATH del sistema")
    
if project_folder.exists(): print(f"Carpeta de proyecto: {project_folder}")
if audio_folder.exists(): print(f"Carpeta de audio: {audio_folder}")
if image_folder.exists(): print(f"Carpeta de imágenes: {image_folder}")
if max_threads: print(f"Procesamiento de medios simultáneos: {max_threads}")
if image_profile_name: print(f"Perfil de compresión de imágenes predeterminado: {image_profile_name}")

##################
# MENU PRINCIPAL #
##################

# TODO
# (Prioridad baja) Agregar opción para configurar flags de cwebp personalizados (para usuarios avanzados)
# (Prioridad baja) Agregar opción para configurar flags de ffmpeg personalizados (para usuarios avanzados)
# (Prioridad ALTA) Modificar comparación de archivos originales y comprimidos para permitir comparar archivos con diferentes extensiones
# (Prioridad media) Agregar opción para detección de archivos cifrados y obtener key de project_folder/data/system.json
# Agregar opción para desencriptar archivos cifrados usando la key obtenida
# Agregar opción para reencriptar archivos desencriptados usando la key obtenida
# Agregar opción para cambiar "hasEncryptedImages":true a false una vez desencriptado los archivos (y su versión de audio correspondiente)
# Agregar opción para abrir herramientas de desencriptación y compresión de terceros
#       https://github.com/uuksu/RPGMakerDecrypter
#       RMDec, UAGC, Enigma unpacker, etc
# Agregar opción para eliminar archivos inútiles detectados (ej: .psd)


while True:
    print("\n" + "="*50)
    print("     MENU PRINCIPAL - COMPRESION DE MEDIOS")
    print("="*50)

    print(f"1 - Seleccionar ruta del proyecto" \
          f"\n    Ruta actual: {(project_folder if project_folder != Path() else "NO SELECCIONADO")}")
    print(f"2 - Menu opciones de calidad de conversión de imágenes" \
          f"\n    Preset actual: {image_profile_name}" \
          f"{"\n    [X] OPCIÓN NO DISPONIBLE" if not cwebp_available else ""}")
    print(f"3 - Iniciar compresión de Imágenes en: " \
          f"{f"\n    {image_folder}" if image_folder != Path() else "[!] No seleccionada"}" \
          f"{"\n    [X] OPCIÓN NO DISPONIBLE" if not image_processing_allowed() else ""}")
    print(f"4 - Iniciar compresión de audio" \
          f"{f"\n    {audio_folder}" if audio_folder != Path() else "[!] No seleccionada"}" \
          f"{"\n    [X] OPCIÓN NO DISPONIBLE" if not audio_processing_allowed() else ""}")
    print(f"5 - Iniciar compresión de imágenes y audio" \
          f"{"\n    [X] OPCIÓN NO DISPONIBLE" if not image_processing_allowed() and not audio_processing_allowed() else ""}")
    print(f"6 - Ejecutar prueba de NW.js del sistema" \
          f"{"\n    [X] OPCIÓN NO DISPONIBLE" if not nwjs_available else ""}")
    print(f"7 - Limpiar NW.js local del directorio del proyecto" \
          f"{"\n    [X] OPCIÓN NO DISPONIBLE" if not nwjs_available else ""}")
    print("0 - Salir del programa")
    try:
        option_main = input(f"Elige una opción (0-7): ").strip()
        option_main = int(option_main)
        if option_main == 0:
            break
        elif option_main == 1:
            project_folder, image_folder, audio_folder = menu_select_project_folder(project_folder, audio_folder, image_folder)
        elif option_main == 2 and image_processing_allowed():
            image_profile_name, cwebp_flags = menu_chose_image_profile(image_profile_name, cwebp_flags)
        elif option_main == 3 and image_processing_allowed():
            image_output = set_output_folder(project_folder, image_folder)
            process_images(image_folder, image_ext, image_output, max_threads, cwebp_flags)
            print("\n---Moviendo Imágenes---")
            replace_originals(image_folder, image_output)
            input("\nTarea Finalizada. Presiona Enter para continuar")
        elif option_main == 4 and audio_processing_allowed():
            audio_output = set_output_folder(project_folder, audio_folder)
            process_audio(audio_folder, audio_ext, audio_output, max_threads)
            print("\n----Moviendo Audio----")
            replace_originals(audio_folder, audio_output)
            input("\nTarea Finalizada. Presiona Enter para continuar")
        elif option_main == 5 and image_processing_allowed() and audio_processing_allowed():
            image_output = set_output_folder(project_folder, image_folder)
            audio_output = set_output_folder(project_folder, audio_folder)
            process_images(image_folder, image_ext, image_output, max_threads, cwebp_flags)
            process_audio(audio_folder, audio_ext, audio_output, max_threads)
            print("\n----Moviendo Media----")
            replace_originals(project_folder, (Path(__file__).parent/"compressed"))
            input("\nTarea Finalizada. Presiona Enter para continuar")
        elif option_main == 6:
            setup_nwjs_game_launcher(project_folder)
            subprocess.run(f"{project_folder / 'nwjs_game_launch.bat'}", cwd=f"{project_folder}")
            print("Juego lanzado")
            # launch_nwjs_game(project_folder)  # Old launch method
        elif option_main == 7:
            remove_files_from_list(project_folder, nwjs_files)
            delete_tree_folder(project_folder/"locales")
            delete_tree_folder(project_folder/"swiftshader")
        else:
            print("Número fuera de rango (0-7).")

    except ValueError:
        print(f"¡Error! Ingresaste algo que no es un número")
    except Exception as e:
        print(f"¡Ocurrió un error inesperado! Detalles del error: {e}")

print("=============================================")
print("Programa terminado. Presione enter para salir")
input("=============================================")
sys.exit()
