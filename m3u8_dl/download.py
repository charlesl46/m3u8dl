from argparse import Namespace
from dataclasses import dataclass, field
import os
from pathlib import Path
from time import sleep
from typing import Any

from m3u8_dl.cli import error, info, warning,CONSOLE
from m3u8_dl.constants import FRENCH_STREAM_BASE_URL
from m3u8_dl.exceptions import FfmpegTooManyRequestsException
from m3u8_dl.ffmpeg import ffmpeg_download, ffmpeg_multiple_download
from m3u8_dl.providers.french_stream import find_download_url, search, transform_endpoint_into_readable
from m3u8_dl.utils import download_file, is_existing_filepath, is_url, read_file, write_lines_to_file
from rich.status import Status
from rich.prompt import IntPrompt
from rich.console import Console
from m3u8_dl.search import search

def download(args : Namespace):
    url_or_filepath_or_query = args.url_or_filepath_or_query

    if args.output:
        output_path = Path(args.output)
        working_dir = output_path.parent
        if output_path.exists():
            error(f"The file at output {output_path} already exists")
    else:
        output_path = Path("output.mp4")
        working_dir = Path(".")

    # dealing with input
    temp_m3u8_path = working_dir.joinpath("output_temp.m3u8")
    if is_url(url_or_filepath_or_query):
        info("Detected url input, fetching url content")
        obj_to_dl = url_or_filepath_or_query
        m3u8_content = download_file(obj_to_dl)

    elif is_existing_filepath(url_or_filepath_or_query):
        info("Detected filepath input, using file content")
        obj_to_dl = Path(url_or_filepath_or_query)
        m3u8_content = read_file(obj_to_dl)
    else:
        info("Detected text query content, searching for corresponding medias")
        query = url_or_filepath_or_query
        nb_results = args.nb_results
        m3u8_url = search(query,nb_results)
        m3u8_content = download_file(m3u8_url)
        write_lines_to_file(temp_m3u8_path,m3u8_content)
        obj_to_dl = temp_m3u8_path

    ffmpeg_path = Path(args.ffmpeg_path)
    wait = args.wait
    nb_parts = args.nb_parts

    try:
        ffmpeg_download(obj_to_dl,output_path,ffmpeg_path)
    except FfmpegTooManyRequestsException:
        warning("The server sent back an HTTP 429 error, trying more slowly")

        if output_path.exists():
            os.remove(output_path)

        with Status(f"Waiting for {wait} seconds" , spinner="dots") as status:
            for i in range(wait):
                sleep(1)
                status.update(f"Waiting for {wait - (i + 1)} seconds")
        try:
            ffmpeg_multiple_download(m3u8_content,output=output_path,working_dir=working_dir,nb_parts=nb_parts,ffmpeg_path=ffmpeg_path)
        except FfmpegTooManyRequestsException:
            error("Couldn't download, try increasing the -w/--wait argument value")

    if temp_m3u8_path.exists():
        os.remove(temp_m3u8_path)
