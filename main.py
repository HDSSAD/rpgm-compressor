import sys, subprocess, shutil, json
from pathlib import Path
from bro_modules import config as bcfg
from bro_modules import system as bsys
from bro_modules import file_manager as bfm
from bro_modules import logger as blog
from bro_modules import image_core
from bro_modules import av_core
from bro_modules import nwjs_core

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
    system_json_path = bfm.select_file(project_folder, "System.json", ".json")
    if system_json_path != None:
        if system_json_path.name.lower() == "system.json" and bfm.subfolder_of(system_json_path, project_folder):
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
        blog.log_exception(e, "update_system_json", "json decode", system_json_path)
    except Exception as e:
        blog.log_exception(e,"update_system_json", "unknown json error", system_json_path)

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
    image_profile_name:str = bcfg.get_default_image_profile_name()
    cwebp_flags:list[str] = bcfg.get_default_cwebp_flags()
    initial_project_size:float = 0.0
    if project_folder != None:
        initial_project_size = bfm.get_folder_size(project_folder)
    project_processed:bool = False
    while True:
        print("="*50)
        print("     MENU PRINCIPAL")
        print("="*50)

        if project_folder != None: 
            print(f"Tamaño inicial del proyecto: {initial_project_size}MB", \
                  f"\nTamaño Actual del proyecto: {bfm.get_folder_size(project_folder)}MB" if project_processed else "")

        options_range:list[int] = [0,1,2]
        print(f"1 - Seleccionar ruta del proyecto. Actual:", f"{project_folder}" if project_folder != None else "NO SELECCIONADA")
        print(f"2 - Menu opciones de calidad de conversión de imágenes. Preset Actual: {image_profile_name}")
        
        if project_folder != None:
            if bsys.image_processing_allowed(project_folder):
                print(f"3 - Iniciar compresión de Imágenes")
                options_range.append(3)
            else: print(f"3 - [X] Compresión de Imágenes no disponible sin cwebp")
            if bsys.audio_processing_allowed(project_folder):
                print(f"4 - Iniciar compresión de audio")
                options_range.append(4)
            else: print(f"4 - [X] Compresión de audio no disponible sin ffmpeg y ffprobe")
            if bsys.video_processing_allowed(project_folder):
                print(f"5 - Iniciar compresión de video")
                options_range.append(5)
            else: print(f"5 - [X] Compresión de video no disponible sin ffmpeg y ffprobe")
            if bsys.image_processing_allowed(project_folder) and bsys.audio_processing_allowed(project_folder):
                print(f"6 - Iniciar compresión de archivos multimedia")
                options_range.append(6)
            else: print(f"6 - [X] Compresión de imágenes y audio no disponible sin apps correspondientes")
            if bfm.get_game_launch_file().exists() and bsys.nwjs_processing_allowed(project_folder):
                print(f"7 - Instalar y configurar {bfm.get_game_launch_file().name}")
                options_range.append(7)
            else: print(f"7 - [X] No se puede Instalar y configurar {bfm.get_game_launch_file().name} si el archivo no existe junto a este script")
            print(f"8 - Limpiar NW.js local del directorio del proyecto")
            options_range.append(8)
        print("9 - Eliminar archivos encriptados")
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
                    new_project_folder = bfm.select_folder("Proyecto")
                    if new_project_folder != project_folder and new_project_folder != None:
                        project_folder = new_project_folder
                        bfm.delete_folder(bfm.get_compressed_folder(project_folder))
                        initial_project_size = bfm.get_folder_size(project_folder)
                        project_processed = False
                elif project_folder != None:
                    if option_main == 2:
                        image_profile_name, cwebp_flags = menu_image_profile(image_profile_name, cwebp_flags)
                    elif option_main == 3:
                        print("Ejecutando tarea de compresión de imágenes...")
                        image_core.process_images(project_folder, cwebp_flags)
                        update_system_json(project_folder, ["hasEncryptedImages"], False)
                        bfm.compare_project_size(project_folder, initial_project_size)
                        bfm.delete_folder(bfm.get_compressed_folder(project_folder))
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 4:
                        print("Ejecutando tarea de compresión de audios...")
                        av_core.process_audios(project_folder)
                        update_system_json(project_folder, ["hasEncryptedAudio"], False)
                        bfm.compare_project_size(project_folder, initial_project_size)
                        bfm.delete_folder(bfm.get_compressed_folder(project_folder))
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 5:
                        print("Ejecutando tarea de compresión de videos...")
                        av_core.process_videos(project_folder, 600)
                        bfm.compare_project_size(project_folder, initial_project_size)
                        bfm.delete_folder(bfm.get_compressed_folder(project_folder))
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 6:
                        print("Ejecutando tarea de compresión de archivos multimedia...")
                        image_core.process_images(project_folder, cwebp_flags)
                        av_core.process_audios(project_folder)
                        av_core.process_videos(project_folder, 600)
                        update_system_json(project_folder, ["hasEncryptedImages", "hasEncryptedAudio"], False)
                        bfm.compare_project_size(project_folder, initial_project_size)
                        bfm.delete_folder(bfm.get_compressed_folder(project_folder))
                        project_processed = True
                        input("\nTarea Finalizada. Presiona Enter para continuar")
                    elif option_main == 7:
                        print("Preparando el entorno del juego...")
                        nwjs_core.setup_nwjs_game_launcher(project_folder)
                        print("nwjs_game_launch instalado y configurado")
                        subprocess.run(f"{project_folder/bfm.get_game_launch_file().name}", cwd=f"{project_folder}")
                        print("Juego lanzado")
                    elif option_main == 8:
                        print(f"Borrando archivos de NW.js locales en {project_folder.name}...")
                        bfm.delete_files_in_list(project_folder, bcfg.get_nwjs_files())
                        bfm.delete_folders_in_list(project_folder, bcfg.get_nwjs_folders())
                        print(f"Archivos locales de NW.js eliminados de {project_folder.name}")
                        bfm.compare_project_size(project_folder, initial_project_size)
                        project_processed = True
                    elif option_main == 9:
                        print(f"Borrando archivos encriptados en {project_folder.name}...")
                        bfm.delete_encrypted_files(project_folder)
                        bfm.compare_project_size(project_folder, initial_project_size)
            else:
                print(f"Número fuera del rango {str(options_range)}.")

        except ValueError:
            print(f"¡Error! Ingresaste algo que no es un número")
        except Exception as e:
            blog.log_exception(e, "Main Menu")
try:
    main_menu(bfm.select_folder("Proyecto"))
except Exception as e:
    input(e)

print("=============================================")
print("Programa terminado. Presione enter para salir")
input("=============================================")
sys.exit()

# TODO
# Agregar nuevo menú para manejar archivos encriptados
# Buscar en System.json: hasEncryptedImages, hasEncryptedAudio, y encryptionKey
# Desencriptar archivos y volver a encriptarlos de ser necesario
# Manejar adecuadamente excepciones marcadas con "# TODO"
# Añadir presets de calidad de video
# Añadir conversión en formato webm
# Probar conversión de audio en opus
# Añadir conversión de audio en mp3 o wav?
# Añadir instalación de dependencias como NWJS, FFMPEG, y CWEBP?
# Otras cosas más...