import subprocess
import exiftool # type: ignore
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path
from bro_modules import config as bcfg
from bro_modules import system as bsys
from bro_modules import file_manager as bfm

def compress_image(project_folder:Path, cwebp_flags:list[str], source:Path) -> tuple[Path,Path]|None:
    # Output será un webp disfrazado de png (u otra extensión del archivo original)
    # para facilitar la aceptación del archivo por parte del motor de RPG Maker y sus scripts
    if source.exists():
        rel_source = source.relative_to(project_folder)
        output = bfm.get_compressed_folder(project_folder)/rel_source
        command:list[str] = cwebp_flags.copy()
        command.append(f"{source}")
        command.append("-o")
        command.append(f"{output}")
        try:
            subprocess.run(command)
        except Exception as e:
            # TODO
            print("ERROR en compress_image subprocess cwebp\n",f"source: {source}\n",f"output: {output}",e)
        return source, output
    return None
# END of function compress_image()

def process_images(project_folder:Path, cwebp_flags:list[str]):
    print("=== Preparando archivos de imágenes ===")
    source_list = bfm.get_source_list(project_folder, bcfg.get_image_extensions())
    to_process_list:list[Path] = get_unoptimized(source_list) if source_list else []
    if to_process_list:
        to_move_list:list[tuple[Path,Path]] = []
        to_mark_list:list[Path] = []
        bfm.create_output_path(project_folder, to_process_list)

        print("=== Iniciando procesamiento de imágenes ===")
        with ThreadPoolExecutor(bsys.get_cpu_threads()) as executor:
            futures = {executor.submit(compress_image, project_folder, cwebp_flags, source)
                    for source in to_process_list}
            for future in tqdm(as_completed(futures), desc="Comprimiendo imágenes", total=len(futures)):
                result = future.result()
                if result:
                    source, compressed = result
                    if source.stat().st_size > compressed.stat().st_size:
                        smaller_file = compressed
                    else:
                        smaller_file = source
                    to_mark_list.append(smaller_file)
                    if smaller_file != source:
                        to_move_list.append((smaller_file, source))

        if to_mark_list:
            print("=== Marcando las imágenes de menos peso (puede demorar) ===")
            mark:str = bcfg.get_custom_mark() # retorna "BROPTIMIZED"
            with exiftool.ExifToolHelper() as et:
                et.set_tags(to_mark_list,  # type: ignore
                            tags={"XMP:UserComment": mark}, 
                            params=["-overwrite_original", "-q"])
        
        if to_move_list:
            print("=== Reemplazando las imágenes más pesadas (puede demorar)===")
            bfm.replace_originals(to_move_list)
# END of function process_images()

def get_unoptimized(source_list:list[Path]) -> list[Path]:
    if source_list:
        mark = bcfg.get_custom_mark() # retorna "BROPTIMIZED"
        tags = ["SourceFile", "XMP:UserComment"]
        mark_tag:str = "XMP:UserComment"
        with exiftool.ExifToolHelper() as et:
            all_metadata:list[dict[str,str]] = list(et.get_tags(source_list, tags=tags)) # type: ignore
        
        new_source_list:list[Path] = []
        for metadata in all_metadata:
            if mark not in str(metadata.get(mark_tag, "")):
                new_source_list.append(Path(metadata["SourceFile"]))
        return new_source_list
    return []


