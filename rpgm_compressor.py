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

# llamado a función comentado en variables globales
def require_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        print("Ejecutando con privilegios de administrador")
    else:
        # Re-ejecutar el script con derechos de administrador
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{__file__}"', None, 1
        )
        sys.exit()
# END of function require_admin()

def check_environment() -> tuple[bool, bool, bool]:
    # Comprobar cwebp en variables de entorno para procesamiento de imágenes
    if shutil.which("cwebp") is None:
        print("[!] No se encontró cwebp en el sistema")
        print("[!] La compresión de imágenes no estará disponible")
        cwebp_available = False
    else:
        print("[+] Compresión de imágenes disponible")
        cwebp_available = True

    # Comprobar ffmpeg y ffprobe en variables de entorno para procesamiento de audio
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("[!] No se encontró ffmpeg o ffprobe en el sistema")
        print("[!] La compresión de audio no estará disponible")
        ffapps_available = False
    else:
        print("[+] Compresión de audio disponible")
        ffapps_available = True

    # Comprobar NW.js en variables de entorno para lanzamiento del juego
    if shutil.which("nw") is None:
        print("[!] No se encontró NW.js en el sistema")
        print("[!] Lanzar el juego con NW.js del sistema no estará disponible")
        print("[!] Para usar NW.js del sistema, por favor descarga NW.js desde https://nwjs.io/ " \
        "y asegúrate de que el ejecutable 'nw' esté en tu PATH del sistema")
        nwjs_available = False
    else:
        print("[+] NW.js detectado en el sistema")
        nwjs_available = True
    
    if not cwebp_available and not ffapps_available and not nwjs_available:
        print("[X] No se encuentran variables de entorno requeridas")
        print("[X] El programa no puede continuar")
        input("Presione Enter para salir...")
        sys.exit()
    return cwebp_available, ffapps_available, nwjs_available


def check_folders() -> tuple[Path, Path, Path, Path]:
    # OBLIGATORIO Seleccionar carpeta de proyecto
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        project_folder = Path(sys.argv[1])
    else:
        tk_root = tk.Tk()
        tk_root.withdraw()
        project_folder = Path(filedialog.askdirectory(title="Selecciona la carpeta del proyecto"))
        tk_root.destroy()
        if project_folder == Path():
            print("[X] El script no puede continuar sin seleccionar carpeta de proyecto")
            print("[X] Cerrando aplicación...")
            sys.exit()

    print(f"[+] Carpeta del Proyecto: {project_folder}")

    # Detectando carpeta de medios predeterminadas
    if (project_folder / "www").exists():
        media_folder = project_folder / "www"
    else:
        media_folder = project_folder

    audio_folder = media_folder / "audio"
    image_folder = media_folder / "img"

    # Seleccionar carpeta de audio manualmente si no se detectan las predeterminadas
    if not audio_folder.exists():
        tk_root = tk.Tk()
        tk_root.withdraw()
        print("No se detectó carpeta de Audio.")
        audio_folder = Path(filedialog.askdirectory(title="Selecciona la carpeta de Audio o cancela para omitir"))
        tk_root.destroy()
        if audio_folder == Path():
            audio_folder_selected = False
        else:
            audio_folder_selected = True
            print(f"[+] Carpeta de Audio seleccionada: {audio_folder}")
    else:
        audio_folder_selected = True

    # Seleccionar carpeta de imágenes manualmente si no se detectan las predeterminadas
    if not image_folder.exists():
        tk_root = tk.Tk()
        tk_root.withdraw()
        print("No se detectó carpeta de Imágenes.")
        image_folder = Path(filedialog.askdirectory(title="Selecciona la carpeta de Imágenes o cancela para omitir"))
        tk_root.destroy()
        if image_folder == Path():
            image_folder_selected = False
        else:
            image_folder_selected = True
            print(f"[+] Carpeta de Imágenes seleccionada: {image_folder}")
    else:
        image_folder_selected = True

    # OBLIGATORIO Debe existir al menos una carpeta de medios
    if not audio_folder_selected and not image_folder_selected:
        print("[X] No se ha detectado ninguna carpeta de medios, el script no puede continuar")
        input("[X] Presione Enter para salir...")
        sys.exit()

    return project_folder, media_folder, audio_folder, image_folder
# END of function check_folders()

# Definimos carpeta de salida para audio
def check_allowed_functions() -> tuple[bool, bool]:
    if ffapps_available and audio_folder.exists():
        print(f"[+] Carpeta de audios detectada en {audio_folder}")
        audio_processing_allowed = True
    else:
        print("[!] No se ha detectado carpeta de Audio")
        audio_processing_allowed = False

    # Definimos carpeta de salida para imagenes
    if cwebp_available and image_folder.exists():
        print(f"[+] Carpeta de imágenes detectada en {image_folder}")
        image_processing_allowed = True
    else:
        print("[!] No se ha detectado carpeta de imágenes")
        image_processing_allowed = False
    
    return audio_processing_allowed, image_processing_allowed
# END of function check_allowed_functions()

def set_folders_output() -> tuple[Path, Path]:
    audio_output = Path(__file__).parent / "compressed/audio"
    image_output = Path(__file__).parent / "compressed/img"
    return audio_output, image_output
# END of function set_folders_output()

# Cantidad de procesos máximos para compresión de medios
def check_cpu_cores() -> int:
    cpu_cores = os.cpu_count()
    if cpu_cores is None:
        max_threads = 2
        print("[!] No se pudo detectar la cantidad de núcleos de CPU, se asignarán 2 procesos simultáneos para la compresión")
    else:
        # Usamos un máximo de núcleos disponibles menos uno, con un límite de 6 para evitar saturar el sistema
        max_threads = max(1, min(cpu_cores - 1, 6))
    print(f"[+] Procesos de converión simultáneos: {max_threads}")
    return max_threads
# END of function check_cpu_cores()

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
                "notification_helper.exe")
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

def replace_originals(original_folder: Path, compressed_folder: Path):
    cumulative_size_saved :int = 0
    cumulative_size_total :int = 0
    for root, dirs, files in compressed_folder.walk():
        for file in files:
            compressed_file = Path(root) / file
            compressed_file_size = compressed_file.stat().st_size
            original_file = original_folder / compressed_file.relative_to(compressed_folder)
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
    except:
        # La carpeta no está vacía, no se puede eliminar
        print(f"[X] No se pudo eliminar {compressed_folder} porque no está vacio")
        print(f"[!] Verifica los archivos en las siguientes carpetas manualmente:")
        print(f"     {compressed_folder}")
        print(f"     {original_folder}")
    
    # Mostrar espacio en disco ahorrado
    print(f"Tamaño de archivos de medios originales: {round(cumulative_size_total/1000000)}MB")
    print(f"Tamaño de archivos de medios comprimidos: {round(cumulative_size_saved/1000000)}MB")
    print(f"Al reemplazar los originales se ha ahorrado en total: {round(cumulative_size_total-cumulative_size_saved)/1000000}MB")
# END function replace_originals()

def chose_image_profile(image_profile_name: str, cwebp_flags: list[str]) -> tuple[str, list[str]]:
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
project_folder, media_folder, audio_folder, image_folder = check_folders()
audio_processing_allowed, image_processing_allowed = check_allowed_functions()
audio_output, image_output = set_folders_output()
image_profile_name, cwebp_flags = default_image_profile()
max_threads = check_cpu_cores()
audio_ext, image_ext, useless_ext, encrypted_ext, nwjs_files, nwjs_folders = detection_filters()

##################
# MENU PRINCIPAL #
##################

# TODO
# (Prioridad baja) Agregar opción para configurar flags de cwebp personalizados (para usuarios avanzados)
# (Prioridad baja) Agregar opción para configurar flags de ffmpeg personalizados (para usuarios avanzados)
# (Prioridad alta) Agregar opción para detección de archivos cifrados y obtener key de project_folder/data/system.json
# Agregar opción para desencriptar archivos cifrados usando la key obtenida
# Agregar opción para reencriptar archivos desencriptados usando la key obtenida
# Agregar opción para abrir herramientas de desencriptación y compresión de terceros
#       https://github.com/uuksu/RPGMakerDecrypter
#       RMDec, UAGC, Enigma unpacker, etc
# Agregar opción para eliminar archivos inútiles detectados (ej: .psd)

while True:
    print("\n" + "="*50)
    print("     MENU PRINCIPAL - COMPRESION DE MEDIOS")
    print("="*50)

    print("1 -", f" [X] NO DISPONIBLE" if not image_processing_allowed else "",\
          f"Configurar calidad de imagen (Actual: {image_profile_name})")
    print("2 -", f" [X] NO DISPONIBLE" if not image_processing_allowed else "",\
          "Iniciar compresión de imágenes")
    print("3 -", f" [X] NO DISPONIBLE" if not audio_processing_allowed else "",\
          "Iniciar compresión de audio")
    print("4 -", f" [X] NO DISPONIBLE" if not image_processing_allowed and not audio_processing_allowed else "",\
        "Iniciar compresión de audio e imágenes")
    print("5 -", f" [X] NO DISPONIBLE" if not nwjs_available else "",\
           "Configurar e iniciar juego con NW.js del sistema")
    print("6 -", f" [X] NO DISPONIBLE" if not nwjs_available else "",\
           "Limpiar NW.js local del directorio del proyecto")
    print("0 - Salir del programa")
    try:
        option_main = input(f"Elige una opción (0-6): ").strip()
        option_main = int(option_main)
        if option_main == 0:
            break
        elif option_main == 1 and image_processing_allowed:
            image_profile_name, cwebp_flags = chose_image_profile(image_profile_name, cwebp_flags)
        elif option_main == 2 and image_processing_allowed:
            process_images(image_folder, image_ext, image_output, max_threads, cwebp_flags)
            print("\n---Moviendo Imágenes---")
            replace_originals(image_folder, image_output)
            input("\nTarea Finalizada. Presiona Enter para continuar")
        elif option_main == 3 and audio_processing_allowed:
            process_audio(audio_folder, audio_ext, audio_output, max_threads)
            print("\n----Moviendo Audio----")
            replace_originals(audio_folder, audio_output)
            input("\nTarea Finalizada. Presiona Enter para continuar")
        elif option_main == 4 and image_processing_allowed and audio_processing_allowed:
            process_images(image_folder, image_ext, image_output, max_threads, cwebp_flags)
            process_audio(audio_folder, audio_ext, audio_output, max_threads)
            print("\n----Moviendo Media----")
            replace_originals(media_folder, (Path(__file__).parent/"compressed"))
            input("\nTarea Finalizada. Presiona Enter para continuar")
        elif option_main == 5:
            setup_nwjs_game_launcher(project_folder)
            subprocess.run(f"{project_folder / 'nwjs_game_launch.bat'}", cwd=f"{project_folder}")
            print("Juego lanzado")
            # launch_nwjs_game(project_folder)  # Old launch method
        elif option_main == 6:
            remove_files_from_list(project_folder, nwjs_files)
            delete_tree_folder(project_folder/"locales")
            delete_tree_folder(project_folder/"swiftshader")
        else:
            print("Número fuera de rango (0-6).")

    except ValueError:
        print(f"¡Error! Ingresaste algo que no es un número. Intentaste procesar: ")
    except NameError as e:
        print(f"¡Error! Parece que no se han definido algunas variables necesarias para esta opción. Detalles del error: {e}")
    except Exception as e:
        print(f"¡Ocurrió un error inesperado! Detalles del error: {e}")

print("=============================================")
print("Programa terminado. Presione enter para salir")
input("=============================================")
sys.exit()