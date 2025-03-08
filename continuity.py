#!/usr/bin/env python3
""" Maintain integrity of downloaded files """
from pathlib import Path
import sys
import subprocess
from typing import Generator

# ffmpeg -v error -i filename.mp4 -vn -c copy -f null - 2>error.log

<<<<<<< HEAD
class ffmpegError(Exception):
    ''' something wrong w/ ffmpeg '''
=======
class FfmpegError(BaseException):
    ''' Error Class pbsk_dl expects '''
    def __init__(self):
        pass
>>>>>>> main

def is_ok(work_path: Path) -> bool:
    """ Fast detection via broken AUDIO stream """
    input_file = str(work_path.absolute())
#    print(f'{work_path.name}')

    proc = ['ffmpeg',
            '-v', 'error',
            '-i',
            input_file,
            '-vn', '-c', 'copy',
            '-f', 'null', 'pipe:']

    with subprocess.Popen(proc,
                          shell=False,
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE
                          ) as process:
        if process.stderr:
            stderr_output = process.stderr.read().decode('utf-8')
            if stderr_output != '':
                print(stderr_output)
                return False

<<<<<<< HEAD
    except ffmpeg.Error as fe:
        stderr = fe.stderr.decode("utf-8")
        print(stderr)
        return False
        pass
=======
        return True
>>>>>>> main


if __name__ == '__main__':
    failures: list = []

    PATH_SOURCE = sys.argv[1]

    def main(path: Path =
             Path(PATH_SOURCE).resolve().absolute()
             ) -> Generator:
        """ Main loop when called by console """
        # print(f'{path=}')
        if path.is_dir():
            print('Path is directory')
            paths_gen = [_ for _ in sorted(path.iterdir())
                         if _.suffix == '.mp4']
            print(f'{paths_gen}')
            for _p in paths_gen:
                # print(f'{_p=}')
                result = is_ok(_p)
                if result is False:
                    failures.append(str(_p))
                yield result
            print(failures)

        elif path.is_file():
            # print('is file')
            yield is_ok(path)
        else:
            yield False
        # yield 'The LSP in my IDE made me :shrug:'

    for i in main():
        print(i)
