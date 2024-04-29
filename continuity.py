#!/usr/bin/env python3
""" Maintain integrity of downloaded files """
from pathlib import Path
import re
import ffmpeg  # type: ignore

"""
ffmpeg -v error -i filename.mp4 -vn -c copy -f null - 2>error.log
"""


def is_ok(workPath: Path) -> bool:
    input_file = str(workPath.with_suffix('.mp4'))
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
        return True
    else:
        return False
