#!/usr/bin/env python3
""" Maintain integrity of downloaded files """
from pathlib import Path
import re
import ffmpeg
from datetime import datetime
from rich import print as rprint

# workDir = Path().home() / "Daniel Tiger's Neighborhood"
workDir = Path().home() / 'external' / 'westley' / 'pbskids' /\
                          "Daniel Tiger's Neighborhood"


""" See if it passes an ffprobe """
for workFile in workDir.iterdir():
    if '.mp4' in workFile.suffixes:
        try:
            """ Get duration from metadata """
            probe = ffmpeg.probe(str(workFile))
            dur_meta = float(probe['format']['duration'])
            # rprint(probe['streams'][0])
            """ Get actual duration from decoding
                https://trac.ffmpeg.org/wiki/FFprobeTips#Getdurationbydecoding
            """

            input_file = str(workFile)

            # capture both stdout and stderr
            process = (
                ffmpeg.input(input_file)
                .output('null', f='null')
                .global_args('-loglevel', 'info')
                .run(capture_stdout=False, capture_stderr=True)
            )
            stderr_output = process[1]
            line = str(stderr_output).split(r'\r')[-1]
            print(line)
            breakpoint()

            # Use a regular expression to find the time value
            match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)

            if match:
                time_str = match.group(1)

                # Parse the time string into a datetime obj
                time_obj = datetime.strptime(time_str,
                                             "%H:%M:%S.%f")

                # Calculate the total seconds
                total_seconds = float(time_obj.hour * 3600 +
                                      time_obj.minute * 60 +
                                      time_obj.second +
                                      time_obj.microsecond /
                                      1000000)

                if abs(total_seconds - dur_meta) < 3:
                    rprint('[bright_green]Pass[/bright_green]')
                else:
                    rprint('[bright_red]Redownload[/bright_red]')
                    print(f"{workFile.name}")

        except Exception:
            raise
