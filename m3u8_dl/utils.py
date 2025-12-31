from pathlib import Path
import random
import re
import requests
import math
import subprocess
import os

def is_url(string : str):
    url_regex = r'(https?://[^\s]+)'
    return re.match(url_regex,string) is not None
    
def is_existing_filepath(string : str):
    try:
        path = Path(string)
    except:
        return False
    
    return path.exists()
    
def time_to_seconds(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.7 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/119.0"
]

def random_user_agent():
    return random.choice(user_agents)

def read_file(filepath : Path) -> list:
    with open(filepath,"r") as file:
        content = file.readlines()
    
    return content

def download_file(url: str) -> list[str]:
    content = []

    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        if r.encoding is None:
            r.encoding = "utf-8"

        for line in r.iter_lines(decode_unicode=True):
            if line:
                content.append(line)

    return content

def write_lines_to_file(filepath : Path,lines : list):
    content = []
    for line in lines:
        if line.endswith("\n"):
            content.append(line)
        else:
            content.append(f"{line}\n")
            
    with open(filepath,"w") as file:
        file.writelines(content)

def count_segments_in_part(part_lines : list):
    segment_lines = [line for line in part_lines if line.startswith("#EXTINF")]
    return len(segment_lines)

def concat_mp4_files(files : list,output : Path,working_dir : Path, ffmpeg_path : Path):    
    outputs_list_filepath = working_dir.joinpath("outputs_list.txt")
    with open(outputs_list_filepath,"w") as output_file:
        for file in files:
            output_file.write(f"file '{str(file)}'\n")
    
    subprocess.run([
        str(ffmpeg_path),
        "-f", "concat",
        "-safe", "0",
        "-i", str(outputs_list_filepath),
        "-c", "copy",
        str(output)
    ],
    stderr=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    check=True)
    
    os.remove(outputs_list_filepath)
    
    
def split_m3u8(lines : list, nb_parts : int) -> list:
    header = []
    segments = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith("#EXTINF"):
            segments.append((line, lines[i + 1]))
            i += 2
        else:
            header.append(line)
            i += 1
    
    total = len(segments)
    chunk_size = math.ceil(total / nb_parts)
    
    outputs = []
    for idx in range(nb_parts):
        start = idx * chunk_size
        end = start + chunk_size
        chunk = segments[start:end]
    
        if not chunk:
            continue
    
        out = []
        out.extend(header)
    
        for extinf, url in chunk:
            out.append(extinf)
            out.append(url)
    
        out.append("#EXT-X-ENDLIST\n")
    
        outputs.append(out)
    
    return outputs
    