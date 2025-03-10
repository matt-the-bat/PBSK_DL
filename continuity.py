#!/usr/bin/env python3
""" Check integrity of downloaded files """
from pathlib import Path
import sys
import subprocess
from typing import Generator

# ffmpeg -v error -i filename.mp4 -vn -c copy -f null - 2>error.log

class FfmpegError(BaseException):
    ''' Error Class pbsk_dl expects '''
    def __init__(self):
        pass

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
    
    print('Checking file integrity')
    with subprocess.Popen(proc,
                          shell=False,
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE
                          ) as process:
        if process.stderr:
            stderr_output = process.stderr.read().decode('utf-8')
            if stderr_output != '':
                #print(stderr_output)
                return False

        return True


if __name__ == '__main__':
    results = {}

    def main(path: Path) -> Generator:
        """ Main loop when called by console """
        # print(f'{path=}')
        if path.is_dir():
            paths_gen = [_ for _ in sorted(path.iterdir())
                         if _.suffix in ['.mp4', '.mpg', '.avi']]
            #print(f'{paths_gen}')
            for _p in paths_gen:
                # print(f'{_p=}')
                yield _p, is_ok(_p)

        elif path.is_file():
            # print('is file')
            yield path, is_ok(path)
        else:
            yield path, False

    for _arg in sys.argv[1:]:
        _arg = Path(_arg).resolve().absolute()
        for inp_path, result in main(_arg):
            results[str(inp_path)] = result
    for _k, _v in results.items():
        print(f'{_k}: {_v}')
