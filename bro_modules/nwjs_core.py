import json, shutil
from pathlib import Path
from bro_modules import file_manager as bfm
from bro_modules import logger as blog

def setup_nwjs_game_launcher(project_folder: Path) -> bool|None:
    """ Realiza la instalación y configuración del launcher personalizado del juego:
    - Crea un directorio para el perfil del juego en una carpeta específica en Local AppData que será la carpeta universal para todos los juegos.
    - Modifica el archivo de configuración json del juego para usar la carpeta creada anteriormente como perfil.
    - Instala el archivo .bat del launcher personalizado dentro de la caerpeta del juego """
    local_appdata: Path | None = bfm.get_localappdata()
    if local_appdata == None:
        print("Selecciona la carpeta Local que está dentro de AppData")
        print("Usualmente en: C:/Users/(tu usuario)/AppData/Local")
        local_appdata = bfm.select_folder("Local AppData")
        if local_appdata == None or local_appdata.name != "Local":
            return
        elif local_appdata.parent.name != "AppData" and not (local_appdata.parent/"LocalLow").exists() and not (local_appdata.parent/"Roaming").exists():
            return
        
    local_appdata= Path(local_appdata)
    rpgm_user_profile: Path = local_appdata/"RPGM/User Data"

    # Borrar todos los archivos en rpgm_user_profile
    if rpgm_user_profile.exists():
        bfm.delete_folder(rpgm_user_profile)
    
    # Si no existe carpeta de perfil, la creamos
    if not rpgm_user_profile.exists():
        rpgm_user_profile.mkdir(parents=True, exist_ok=True)

    # Update package.json
    package_json_path: Path = project_folder / "package.json"
    if not package_json_path.exists():
        package_json_path = project_folder / "www" / "package.json"
        if not package_json_path.exists():
            print("No se encontró package.json en el proyecto. Asegúrate de seleccionar la carpeta correcta del proyecto")
    
    if package_json_path.exists():
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
            blog.log_exception(e, "setup_nwjs_game_launcher", "json decode", package_json_path)
        except Exception as e:
            blog.log_exception(e,"setup_nwjs_game_launcher", "unknown json error", package_json_path)
        # Update package.json END

    nwjs_game_launcher: Path = bfm.get_script_folder() / "nwjs_game_launch.bat"
    if not nwjs_game_launcher.exists():
        print("[X] No se encontró el script de lanzamiento del juego con NW.js del sistema")
        print("[X] Asegúrate de que nwjs_game_launch.bat esté en la misma carpeta que este script")
        return
    else:
        # Copiamos el archivo nwjs_game_launch.bat a la carpeta del proyecto
        try:
            shutil.copy(nwjs_game_launcher, project_folder / "nwjs_game_launch.bat")
            print(f"[+] Script de NWJS Game Launcher copiado a {project_folder}")
            return True
        except Exception as e:
            blog.log_exception(e, "setup_nwjs_game_launcher", "shutil copy error", nwjs_game_launcher)
# END of function install_nwjs_game_launch()