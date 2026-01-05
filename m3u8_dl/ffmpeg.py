import os
import re
import subprocess
import threading
from m3u8_dl.constants import NB_PARTS
from pathlib import Path
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn,SpinnerColumn
from m3u8_dl.cli import CONSOLE, info
from m3u8_dl.exceptions import FfmpegTooManyRequestsException
from m3u8_dl.utils import concat_mp4_files, count_segments_in_part, download_file, random_user_agent, read_file, split_m3u8, time_to_seconds, write_lines_to_file
from time import sleep

def ffmpeg_download(object_to_download : str,output : Path,ffmpeg_path : Path):
    cmd = [
        str(ffmpeg_path),
        "-protocol_whitelist",
        "file,crypto,data,http,https,tcp,tls",
        "-i", object_to_download,
        "-user_agent", random_user_agent(),
        "-bsf:a", "aac_adtstoasc",
        "-vcodec", "copy",
        "-c", "copy",
        "-crf", "50",
        str(output)
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        universal_newlines=True
    )

    total_duration = None
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>5.1f}%"),
        TimeRemainingColumn(),
        console=CONSOLE,
        transient=True
    ) as progress:

        task_id = progress.add_task("Download in progress", total=100)

        for line in process.stderr:
            line = line.strip()

            # detecting error
            if "error 429" in line:
                process.kill()
                raise FfmpegTooManyRequestsException

            if total_duration is None:
                m = re.search(r"Duration: (\d+:\d+:\d+\.\d+)", line)
                if m:
                    total_duration = time_to_seconds(m.group(1))
                    progress.update(task_id, total=total_duration)
                    continue

            m = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
            if m and total_duration:
                current = time_to_seconds(m.group(1))
                progress.update(task_id, completed=current)

    process.wait()
    
    info("Done ! Leaving")


def parse_ffmpeg_progress(process, task_id, progress):
    total_duration = None
    for line in process.stderr:
        line = line.strip()

        if "error 429" in line.lower():
            process.kill()
            raise FfmpegTooManyRequestsException()

        if total_duration is None:
            m = re.search(r"Duration: (\d+:\d+:\d+\.\d+)", line)
            if m:
                total_duration = time_to_seconds(m.group(1))
                progress.update(task_id, total=total_duration)
                continue

        if total_duration:
            m = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
            if m:
                current = time_to_seconds(m.group(1))
                progress.update(task_id, completed=current)
    
    progress.update(task_id, description=f"[bold green]{progress.tasks[task_id].description.split(' ')[0]} completed[/bold green]",completed=progress.tasks[task_id].total)

def ffmpeg_multiple_download(m3u8_content : list,output : Path,working_dir : Path,nb_parts : int, ffmpeg_path : Path):
    info(f"Splitting m3u8 file in {nb_parts} parts")
    m3u8_parts = split_m3u8(m3u8_content,nb_parts)

    processes = []
    part_m3u8_files = []
    part_mp4_files = []
    threads = []
    
    info(f"Downloading {NB_PARTS} parts in parallel")
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        transient=True,
        console=CONSOLE
    ) as progress:

        for i, part in enumerate(m3u8_parts):
            index = i + 1
            m3u8_part_file = working_dir / f"output_part{index}.m3u8"
            write_lines_to_file(m3u8_part_file, part)
            part_m3u8_files.append(m3u8_part_file)
            
            nb_segments = count_segments_in_part(part)

            part_output = working_dir / f"output_part{index}.mp4"
            part_mp4_files.append(part_output)

            cmd = [
                str(ffmpeg_path),
                "-protocol_whitelist",
                "file,crypto,data,http,https,tcp,tls",
                "-re",
                "-i", str(m3u8_part_file),
                "-user_agent", random_user_agent(),
                "-bsf:a", "aac_adtstoasc",
                "-vcodec", "copy",
                "-c", "copy",
                "-crf", "50",
                str(part_output)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            processes.append(process)
            task_id = progress.add_task(f"Part {index} ({nb_segments} segments)", total=100)
            
            t = threading.Thread(target=parse_ffmpeg_progress, args=(process, task_id, progress))
            t.start()
            threads.append(t)
        
        for p in processes:
            p.wait()
            
        for t in threads:
            t.join()
            
    info("Cleaning m3u8 files")
    for file in part_m3u8_files:
        os.remove(file)
        
    info(f"Concatenating {len(part_mp4_files)} mp4 files into one at {str(output)}")
    concat_mp4_files(part_mp4_files,output,working_dir,ffmpeg_path)
    
    info("Cleaning mp4 files")
    for file in part_mp4_files:
        os.remove(file)

    info("Done ! Leaving")