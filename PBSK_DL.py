#!/usr/bin/env python3
"""Examples: 'peg-cat', 'daniel-tigers-neighborhood'"""
import sys
import urllib.request
import json
from pathlib import Path
from typing import List, Dict
import time
import argparse
from pycaption import (  # type: ignore
    CaptionConverter,
    detect_format,
    SAMIReader,
    DFXPReader,
    WebVTTReader,
    SRTWriter,
)

import continuity
import find_shows


output_root = Path.cwd()
# output_root = Path.home()


def mapchars(_x: str) -> str:
    ''' Map of characters to replace file names with '''
    charmap = {
        "/": "; ",
        ": ": "_",
        "?": "",
        r"\\": "",
        "*": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "",
        r"'\''s": r"'s",
    }
    for _k, _v in charmap.items():
        _x = _x.replace(_k, _v)
    return _x


class Subtitle:
    """ Contains cc_ url, ext, and type variables
        for handling subs"""

    def __init__(self, cc_avail):
        """ Examines a list of caption dictionaries,
        and assigns to the instance variables:
        - cc_url: the subtitle URL,
        - cc_ext: the file extension,
        - cc_type: the caption type (format).

        The method prioritizes "SRT" and checks against a
        predefined set of supported formats.

        Args:
            captions (List[Dict]): List of caption dictionaries.
                                    Each dictionary should have at
                                    least the keys 'format' and 'URI'.
        """
        self.cc_avail = cc_avail
        self.cc_url = ''
        self.cc_ext = ''
        self.cc_type = ''

        self.sub_check(cc_avail)

    def sub_check(self, cc_avail: List[Dict]):
        """Captions/Subtitles Check """
        cc_exts = {
            "SRT": "srt",
            "WebVTT": "vtt",
            "DFXP": "dfxp",
            "Caption-SAMI": "sami",
        }

        if cc_avail is None:
            cc_avail = self.cc_avail

        chosen_cap = None

        # First pass: try to locate an SRT caption.
        for cap in cc_avail:
            current_format = cap.get("format", "")
            if "SRT" in current_format:
                self.cc_type = current_format
                self.cc_url = cap.get("URI", "")
                chosen_cap = cap
                break  # Stop at the first SRT found

        # If no SRT was found, look for any supported caption format.
        if not chosen_cap:
            for cap in cc_avail:
                current_format = cap.get("format", "")
                if current_format in cc_exts:
                    self.cc_type = current_format
                    self.cc_url = cap.get("URI", "")
                    chosen_cap = cap
                    break
                else:
                    print(f"No supported subtitle: {cap}")

        # Set the file extension based on the chosen caption format.
        if chosen_cap:
            self.cc_ext = cc_exts.get(self.cc_type, "")
        else:
            self.cc_ext = ''

    def any2srt(self, out_title: Path) -> None:
        """Converts any subtitle to srt.
        https://pycaption.readthedocs.io/en/stable/introduction.html """

        caps = ""
        with open(out_title.with_suffix(f".{self.cc_ext}"),
                  encoding="utf-8") as _fd:
            caps = _fd.read()

        reader = detect_format(caps)
        if reader:
            with open(f"{out_title}.srt", "w",
                      encoding='utf-8') as _fe:
                _fe.write(SRTWriter().write(reader().read(caps)))

        else:
            print("No sub type found")

    def sub_download(self, out_title: Path):
        """out_title is name of file, minus suffix"""
        try:
            sub_path = out_title.with_suffix("." + self.cc_ext)
            urllib.request.urlretrieve(self.cc_url, str(sub_path))
            if self.cc_ext != "srt":
                # Convert webvtt to srt, because
                # Kodi 19 will crash on presence of a webvtt file
                self.any2srt(out_title)
                out_title.with_suffix(f".{self.cc_ext}").unlink()

        except Exception:
            print('What')
            raise  # what to do here?


def download_file(url, length, filename, rate_limit=2048):
    """rate_limit in kilobytes"""
    if length is None:
        length = 0
    start_time = time.time()
    rate_limit = rate_limit * 1024
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        downloaded = 0

        with open(filename, "wb") as file:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                file.write(chunk)
                downloaded += len(chunk)
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    current_rate = downloaded / elapsed_time / 1024
                    if current_rate > rate_limit:
                        time.sleep(
                            (downloaded / rate_limit / 1024) - elapsed_time
                        )
                    start_time = time.time()

                # Update the progress bar
                progress_bar = "\rDownloaded: {:.2f} MB of {} MB".format(
                    downloaded / (1024 * 1024),
                    int(length) // 1024 // 1024
                )
                sys.stdout.write(progress_bar)
                sys.stdout.flush()

    # Print a newline after the progress bar
    print()


def iter_episodes(jcontent: Dict):
    ''' Download using json file contents '''
    for item_jcontent in jcontent["collections"]["episodes"]["content"]:
        show_name = item_jcontent["program"]["title"]
        air_date = item_jcontent["air_date"][0:10]
        ep_title = mapchars(item_jcontent["title"])
        ep_title = ep_title.replace("/", "+")  # Slash be gone
        print(ep_title)

        out_dir: Path = Path(output_root, show_name)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_title: Path = Path(out_dir, f"{air_date} - {ep_title}")
        out_mp4: Path = out_title.with_suffix(".mp4")

        # Save .json
        with open(out_title.with_suffix(".json"), "w",
                  encoding="utf-8") as _fd:
            json.dump(jcontent, _fd)
        try:
            mp4 = item_jcontent["mp4"]  # Video file URL
            # RESPONSE TESTING FOR CONTENTLENGTH
            req = urllib.request.Request(mp4)
            with urllib.request.urlopen(req) as response:
                content_length = response.headers["Content-Length"]
            # break
            # END RESPONSE TESTING
        except FileNotFoundError:
            print("No valid mp4!")
            raise
        # Prevent re-downloading existing mp4
        if out_mp4.is_file():
            if continuity.is_ok(out_mp4) is False:
                print("Redownloading partial download")
                out_mp4.unlink()
                download_file(mp4, content_length, f"{out_mp4}")
        else:
            print("Downloading...")

            download_file(mp4, content_length, f"{out_mp4}")
            try:
                continuity.is_ok(out_mp4)
            except continuity.FfmpegError as exc:
                raise continuity.FfmpegError from exc

        # Captions/Subtitles Check
        sub_obj = Subtitle(item_jcontent["closedCaptions"])
        sub_obj.sub_download(out_title)


def main(show):
    """Examples: 'peg-cat', 'daniel-tigers-neighborhood'"""
    # Retrieve show information
    urlroot = "https://content.services.pbskids.org/v2/kidspbsorg/programs/"
    with urllib.request.urlopen(urlroot + show,
                                ) as proc:
        contents = json.loads(proc.read())
    iter_episodes(contents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download the episodes of a pbs kids show"
    )
    parser.add_argument(
        "show",
        # default="jelly-ben-pogo",
        nargs="?",
        help="show name. default daniel-tigers-neighborhood",
    )
    parser.add_argument(
        "-r",
        "--rate-limit",
        required=False,
        type=int,
        default=10 * 1024 * 1024,
        help="Rate limit in bytes per second (default: 10 MB/s)",
    )

    args = parser.parse_args()

    if not args.show:
        print('Pick one of these shows:')
        find_shows.run()
    else:
        main(args.show)
