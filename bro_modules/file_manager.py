import shutil, os
import tkinter as tk
from tqdm import tqdm
from tkinter import filedialog
from pathlib import Path
from bro_modules import logger as blog
from bro_modules import config as bcfg

def get_localappdata() -> Path|None:
    """ Devuelve un Path con la dirección de la carpeta ~/AppData/Local, y si no la encuentra devuelve un Path vacio """
    local_appdata: str | None = os.getenv("LOCALAPPDATA")
    if local_appdata == None:
        return None
    return Path(local_appdata)

def get_script_folder() -> Path:
    """ Devuelve la ruta actual del programa principal """
    return Path(__file__).parent.parent

def get_logs_folder() -> Path:
    """ Devuelve la ruta hacia la carpeta logs del programa """
    logs_folder: Path = get_script_folder()/"logs"
    if not logs_folder.exists():
        logs_folder.mkdir(parents=True, exist_ok=True)
    return logs_folder

def get_game_launch_file() -> Path:
    """ Devuelve la ruta hacia el lanzador del juego junto al programa """
    return get_script_folder()/"nwjs_game_launch.bat"
    
def get_folder_size(folder:Path) -> float:
    """ Recorre una carpeta y devuelve el peso en MB de todo su contenido """
    size:float = sum(file.stat().st_size for file in folder.rglob('*') if file.is_file())
    size = round(size/(1024*1024), ndigits=2)
    return size

def subfolder_of(folder:Path, parent:Path) -> bool:
    if str(parent) in str(folder):
        return True
    return False

def get_compressed_folder(project_folder:Path) -> Path:
    """ Devuelve la ruta de la carpeta compressed del programa, y la crea si no existe """
    compressed_folder: Path = project_folder.parent/"broptimized_temp"
    if not compressed_folder.exists():
        compressed_folder.mkdir(parents=True, exist_ok=True)
    return compressed_folder

def create_output_path(project_folder:Path, source_file_list:list[Path]):
    for source_file in source_file_list:
        rel_source_file: Path = source_file.relative_to(project_folder)
        output_file: Path = get_compressed_folder(project_folder)/rel_source_file
        if not output_file.parent.exists():
            output_file.parent.mkdir(parents=True, exist_ok=True)

def select_folder(folder_type: str) -> Path|None:
    """ Abre la ventana de dialogo de selección de directorios """
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_folder: str = filedialog.askdirectory(title=f"Selecciona la carpeta de {folder_type} o cancela para omitir")
    tk_root.destroy()
    if len(selected_folder) == 0:
        return None
    return Path(selected_folder)

def select_file(project_folder:Path, file_name:str, extension:str) -> Path|None:
    """ Abre la ventana de dialogo de selección de archivos """
    tk_root = tk.Tk()
    tk_root.withdraw()
    selected_file: str = filedialog.askopenfilename(title=f"Selecciona el archivo {file_name} correspondiente", filetypes=[(f"{extension}",f"{extension}")], initialdir=str(project_folder))
    tk_root.destroy()
    if len(selected_file) == 0:
        return None
    return Path(selected_file)

def delete_folder(folder:Path):
    """ Toma un directorio elimina todo su contenido """
    if folder.exists():
        try:
            shutil.rmtree(folder, ignore_errors=True)
            print(f"Eliminado directorio: {folder}")
        except Exception as e:
            blog.log_exception(e, "delete_folder", "rmtree in delete_folder", folder)

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
                        blog.log_exception(e, "delete_files_in_list", "file unlink", file_path)
    return files_size

def delete_folders_in_list(folder: Path, folders_to_remove: tuple[str,...]) -> float:
    """ Toma un directorio y una lista, busca en el directorio los nombres de directorios que se encuentren en la lista y los elimina """
    folder_size:float = 0.0
    for root, dirs, _ in folder.walk():
        for dir in dirs:
            if dir in folders_to_remove:
                current_folder: Path = (root/dir)
                if current_folder.exists():
                    folder_size += get_folder_size(current_folder)
                    try:
                        shutil.rmtree(current_folder, ignore_errors=True)
                        print( f"Eliminado directorio: {current_folder}")
                    except Exception as e:
                        blog.log_exception(e, "delete_folders_in_list", "rmtree in delete_folder", current_folder)
    return folder_size

def compare_project_size(project_folder:Path, initial_project_size:float):
    # Mostrar espacio en disco ahorrado
    new_size: float = get_folder_size(project_folder)
    print("")
    print(f"Tamaño del proyecto originalmente:.....{initial_project_size}MB")
    print(f"Espacio Ahorrado hasta ahora:..........{round(initial_project_size-new_size, ndigits=2)}MB")
    print(f"Tamaño actual del proyecto:............{new_size}MB")

def get_source_list(project_folder:Path, extensions:tuple[str,...]) -> list[Path]:
    source_file_list:list[Path] = []
    for root, _, files in project_folder.walk():
        for file in files:
            if file.lower().endswith(extensions):
                source_file_list.append(root/file)
    return source_file_list

def replace_originals(to_move_list:list[tuple[Path,Path]]):
    print("- Reemplazando los archivos más pesados")
    exception_list:list[dict[str,Exception]] = []
    for file_pair in tqdm(to_move_list,
                          desc="Reemplazando archivos",
                          total=len(to_move_list)):
        smaller_file, source = file_pair
        if smaller_file.exists():
            try:
                smaller_file.replace(source)
            except Exception as e:
                exception_list.append({str(smaller_file)+"\n":e})
    # Mostrar errores al final
    if exception_list:
        print("Ocurrió un problema al mover los siguientes archivos:")
        for except_data in exception_list:
            print(f"[X] {except_data}")
        print("")

def delete_encrypted_files(project_folder:Path):
    for root, _, files in project_folder.walk():
        for file in files:
            if file.lower().endswith(bcfg.get_encrypted_extensions()):
                file_path: Path = root/file
                try:
                    file_path.unlink(missing_ok=True)
                except Exception as e:
                    print("ERROR, del_encrypted_files, file.unlink\n", e)
                # end try