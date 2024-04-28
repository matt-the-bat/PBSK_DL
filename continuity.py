#!/usr/bin/env python3
""" Maintain integrity of downloaded files """
from pathlib import Path
import re
import ffmpeg  # type: ignore
from rich import print as rprint

# workDir = Path().home() / "Daniel Tiger's Neighborhood"
workDir = Path().home() / 'external/westley/pbskids' /\
                          "Daniel Tiger's Neighborhood"

"""
ffmpeg -v error -i filename.mp4 -vn -c copy -f null - 2>error.log
"""
for workFile in sorted(workDir.iterdir()):
    if '.mp4' in workFile.suffixes:
        try:
            input_file = str(workFile)
            rprint(workFile.name)
            # Broken audio stream is fast to detect
            audio_stream = ffmpeg.input(input_file).audio
            process = \
                (
                    ffmpeg
                    .output(audio_stream,
                            'null', f='null', c='copy')
                    .global_args('-loglevel', 'error')
                    .run(capture_stdout=False,
                         capture_stderr=True)
                 )
            stderr_output = process[1]
            line = str(stderr_output).split(r'\r')[-1]

            match_obj = re.search(r'partial file', line)

            if not match_obj:
                rprint('[bright_green]Pass[/bright_green]')
            else:
                rprint('[bright_red]Redownload[/bright_red]')
                print(f"{workFile.name}")

        except:
            raise
