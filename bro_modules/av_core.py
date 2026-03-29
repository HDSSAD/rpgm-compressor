import subprocess, os
import ffmpeg # type: ignore
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from bro_modules import system as bsys
from bro_modules import file_manager as bfm
from bro_modules import config as bcfg

def process_videos(project_folder:Path, quality:int = 600, plus:int|float = 1.15):
    """ Inicia el procesamiento en paralelo de videos dentro de project_folder\n
    """
    print("- Preparando archivos de videos")
    source_list: list[Path] = bfm.get_source_list(project_folder, bcfg.get_video_extensions())
    if not source_list:
        print("[!] No hay archivos de video que procesar")
        return

    to_process_list:list[Path] = get_to_process_list(source_list) if source_list else []
    if not to_process_list:
        print("[!] Todos los videos ya han sido optimizados")
        return
    
    bfm.create_output_path(project_folder, to_process_list)
    to_mark_list:list[Path] = []
    to_move_list:list[tuple[Path,Path]] = []

    print("- Iniciando procesamiento de videos")
    # Limitación a 1 hilo para convertir videos debido a que el procesamiento de videos es más pesado
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(compress_video, project_folder, quality, plus, source) for source in to_process_list}
        for future in tqdm(as_completed(futures), desc="Comprimiendo videos", total=len(futures)):
            result: tuple[Path, Path] | None = future.result()
            if result:
                source, compressed = result
                if source.stat().st_size > compressed.stat().st_size:
                    smaller_file = compressed
                else:
                    smaller_file = source
                if smaller_file != source:
                    to_move_list.append((smaller_file, source))
                else:
                    to_mark_list.append(smaller_file)

    if to_mark_list:
        print("- Marcando los videos originales de menor peso")
        mark_files(to_mark_list)

    return to_move_list
        
# END of function process_videos()

def process_audios(project_folder:Path) -> list[tuple[Path,Path]]|None:
    """ Inicia el procesamiento en paralelo de audios dentro de project_folder\n
    """
    print("- Preparando archivos de audio")
    source_list: list[Path] = bfm.get_source_list(project_folder, bcfg.get_audio_extensions())
    if not source_list:
        print("[!] No hay archivos de audio que procesar")
        return

    to_process_list:list[Path] = get_to_process_list(source_list) if source_list else []
    if not to_process_list:
        print("[!] Todos los audios ya han sido optimizados")
        return
    
    bfm.create_output_path(project_folder, to_process_list)
    to_mark_list:list[Path] = []
    to_move_list:list[tuple[Path,Path]] = []

    print("- Iniciando procesamiento de audios")
    with ThreadPoolExecutor(bsys.get_cpu_threads()) as executor:
        futures = {executor.submit(compress_audio, project_folder, source)
                for source in to_process_list}
        for future in tqdm(as_completed(futures), desc="Comprimiendo audios", total=len(futures)):
            result: tuple[Path, Path] | None = future.result()
            if result:
                source, compressed = result
                if source.stat().st_size > compressed.stat().st_size:
                    smaller_file: Path = compressed
                else:
                    smaller_file: Path = source
                if smaller_file != source:
                    to_move_list.append((smaller_file, source))
                else:
                    to_mark_list.append(source)
    
    if to_mark_list:
        print("- Marcando los audios originales de menor peso")
        mark_files(to_mark_list)

    return to_move_list
# END of function process_audios()

def get_to_process_list(source_list:list[Path]) -> list[Path]:
    to_process_list:list[Path] = []
    with ThreadPoolExecutor(bsys.get_cpu_threads()) as executor:
        futures = {executor.submit(get_unoptimized, file)
                for file in source_list}
        for future in tqdm(as_completed(futures),
                        desc="Listando archivos",
                        total=len(futures)):
            result: Path | None = future.result()
            if result:
                to_process_list.append(result)
    return to_process_list

def get_unoptimized(file:Path) -> Path|None:
    if not file.exists():
        return None
    try:
        metadata = ffmpeg.probe(file) # type: ignore
        if bcfg.get_custom_mark() not in str(metadata):
            return file
        return None
    except Exception as e:
        print("ERROR, get_unoptimized, ffprobe\n", e)
        return None
    # end try

def mark_files(to_mark_list:list[Path]):
    max_threads: int = bsys.get_cpu_threads()
    with ThreadPoolExecutor(max_threads) as executor:
        futures = {executor.submit(mark_as_optimized, file) 
                    for file in to_mark_list}
        for _ in tqdm(as_completed(futures), 
                            desc="Marcando archivos", 
                            total=len(futures)):
            pass

def mark_as_optimized(file:Path) -> bool:
    """ Copia el flujo de datos (sin recodificar) y añade el tag BROPTIMIZADO.
    """
    mark: str = bcfg.get_custom_mark()
    output: Path = file.with_stem(f"{file.stem}_broptimized")

    cmd:list[str] = [
        "ffmpeg", "-hide_banner", "-v", "quiet",
        "-y",                                   # Sobreescribe archivos de salida
        "-i", str(file),
        "-c", "copy",                           # Copia exacta de audio/video/imagen
        "-map_metadata", "0",                   # Mantiene metadatos originales
        "-metadata", f"comment={mark}",         # Añade la marca
        str(output)
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        file.unlink()
        output.rename(file)
        return True
    except Exception as e:
        # TODO
        print("ERROR in mark_as_optimized subprocess, unlink, rename", e)
        return False
    # end try
# END of function mark_as_optimized()

def compress_video(project_folder:Path, quality:int, plus:int|float, source:Path) -> tuple[Path,Path]|None:
    if not source.exists():
        return None
    
    mark: str = bcfg.get_custom_mark()
    rel_source: Path = source.relative_to(project_folder)
    output: Path = bfm.get_compressed_folder(project_folder)/rel_source.with_suffix(".mp4")
    target_res, video_bitrate, vf_scale = optimal_video_quality(source, quality, plus)

    if min(target_res, video_bitrate) == 0 or vf_scale == "":
        return None
    
    audio_bitrate = "48"
    audio_codec = "libopus"
    extra: list[str] = ["-pix_fmt", "yuv420p", "-ar", "48000", "-tune", "animation"]
    video_codec = "libx264"

    passlog = "ffmpeg_pass_temp"
    null:str = "NUL" if os.name == "nt" else "/dev/null"

    cmd1:list[str] = [
        "ffmpeg", "-hide_banner", "-v", "quiet",
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
        return None
    # end try

    # Pass 2
    cmd2:list[str] = [
        "ffmpeg", "-hide_banner", "-v", "quiet",
        "-i", str(source),
        "-vf", f"scale={vf_scale}",
        "-c:v", video_codec,
        "-preset", "medium",
        *extra,
        "-b:v", f"{video_bitrate}k",
        "-pass", "2",
        "-passlogfile", passlog,
        "-c:a", audio_codec,
        "-b:a", f"{audio_bitrate}k",
        "-y",                                   # Sobreescribe archivos de salida
        "-map_metadata", "0",                   # Mantiene metadatos originales
        "-metadata", f"comment={mark}",         # Añade la marca
        str(output)
    ]
    try:
        subprocess.run(cmd2, check=True)
    except subprocess.CalledProcessError as e:
        print("Falló Pass 2", e)
        return None
    # end try
    # Limpieza
    for passlog_file in [f"{passlog}-0.log", f"{passlog}-0.log.mbtree"]:
        passlog_file = Path(passlog_file)
        if passlog_file.is_file():
            passlog_file.unlink()
    return source, output
# END of function compress_video()

def compress_audio(project_folder:Path, source:Path) -> tuple[Path, Path]|None:
    """ Ejecuta ffmpeg para comprimir el archivo de audio.

    Devuelve una tupla de source y output (original, comprimido)
    """
    if not source.exists():
        return None
    
    mark: str = bcfg.get_custom_mark()
    rel_source: Path = source.relative_to(project_folder)
    output: Path = bfm.get_compressed_folder(project_folder)/rel_source
    output = output.with_suffix(".ogg")
    hz: int = get_audio_hz(source)
    if 22050 <= hz < 32000:
        hz = 22050
    else:
        hz = 32000
    cmd:list[str] = [
            "ffmpeg", "-hide_banner", "-v", "quiet",
            "-i", f"{source}",
            "-c:a", "libvorbis", 
            "-ar", f"{hz}", 
            "-q:a", "0", 
            "-y",                                   # Sobreescribe archivos de salida
            "-map_metadata", "0",                   # Mantiene metadatos originales
            "-metadata", f"comment={mark}",    # Añade una marca
            f"{output}"
        ]
    try:
        subprocess.run(cmd, check=True)
        return source, output
    except Exception as e:
        # TODO
        print("ERROR en compress_audio subprocess",e)
        return None
# END of function compress_audio()

def get_audio_hz(file: Path) -> int:
    """ Analiza un archivo de audio con ffprobe y devuelve sus hz o 0 si hay error """
    metadata = ffmpeg.probe(str(file)) # type: ignore
    if "sample_rate" in metadata:
        try:
            sample_rate = metadata.get("streams")[0].get("sample_rate", "0")
        except Exception:
            sample_rate = "0"
        # end try
        return int(sample_rate)
    return 0

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
        vf_scale: str = f"-2:{target_res}"
    else:
        vf_scale: str = f"{target_res}:-2"

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

def get_video_kbps(file:Path) -> int:
    metadata = ffmpeg.probe(str(file)) # type: ignore
    if "bit_rate" in metadata:
        try:
            bit_rate = int(metadata.get("streams")[0].get("bit_rate", 0))
        except Exception as e:
            print("Ocurrió un error inesperado - get_video_bitrate()", e)
            bit_rate = 0
        # end try
        return int(bit_rate/1000)
    return 0

def optimal_kbps_for_resolution(quality:int, plus:float|int = 1.15) -> int:
    return int(((quality ** 2 / 180)  - (15/4) * quality + 1020)*plus)

def get_video_resolution(file:Path) -> tuple[int, int]:
    """
    Obtiene la resolución de un video usando ffprobe.
    Retorna ancho y alto si se completó con éxito, None si algo falló.
    """
    try:
        metadata = ffmpeg.probe(str(file)) # type: ignore
        width = int(metadata.get("streams")[0].get("width", 0))
        height = int(metadata.get("streams")[0].get("height", 0))
        if width == 0 or height == 0:
            return 0,0
        return width, height
    except Exception as e:
        print("Ocurrió un error inesperado - get_video_resolution()", e)
        return 0,0
# END of function get_video_resolution()