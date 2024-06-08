#!/usr/bin/env python3
""" Maintain integrity of downloaded files """
from pathlib import Path
import re
import ffmpeg  # type: ignore
import sys
from typing import Generator
"""
ffmpeg -v error -i filename.mp4 -vn -c copy -f null - 2>error.log
"""


class ffmpegError(Exception):
    ''' something wrong w/ ffmpeg '''


def is_ok(workPath: Path) -> bool:
    """ Fast detection via broken AUDIO stream """
    input_file = str(workPath)
    print(f'{workPath.name}')
    audio_stream = ffmpeg.input(input_file).audio
    try:
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

    except ffmpeg.Error as fe:
        stderr = fe.stderr.decode("utf-8")
        print(stderr)
        return False
        pass


if __name__ == '__main__':
    failures: list = []

    def main(path: Path =
             Path(sys.argv[1]).resolve().absolute()
             ) -> Generator:
        # print(f'{path=}')
        if path.is_dir():
            print('Path is directory')
            paths_gen = [_ for _ in sorted(path.iterdir())
                         if _.suffix == '.mp4']
            # print(f'{paths_gen}')
            for p in paths_gen:
                # print(f'{p=}')
                result = is_ok(p)
                if result is False:
                    failures.append(str(p))
                yield result
            yield failures

        elif path.is_file():
            # print('is file')
            yield is_ok(path)
        elif not path.exists():
            raise FileNotFoundError(f'No such file as {path.name}')
        else:
            yield False
        # yield 'The LSP in my IDE made me :shrug:'

    for i in main():
        # print(i)
        if type(i) == list:
            print(i)
