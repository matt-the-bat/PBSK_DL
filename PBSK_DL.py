#!/usr/bin/env python3
"""Examples: 'peg-cat', 'daniel-tigers-neighborhood'"""
import sys
import urllib.request
import json
from pathlib import Path
from typing import List, Dict, Tuple
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

# TODO rewrite as class and tuple becomes named obj variables


def sub_check(
    _i: List[Dict],
    cc_exts: Dict = {
        "SRT": "srt",
        "WebVTT": "vtt",
        "DFXP": "dfxp",
        "Caption-SAMI": "sami",
    },
) -> Tuple[str, str, str]:  # url, ext, type
    """Captions/Subtitles Check
    TODO: Returns EXT/subtitletype ?"""
    if cc_exts is None:
        cc_exts = {
            "SRT": "srt",
            "WebVTT": "vtt",
            "DFXP": "dfxp",
            "Caption-SAMI": "sami",
        }

    for cap in _i:
        cc_type = cap["format"]
        cc_url = ""
        if "SRT" in cc_type:
            cc_url = cap["URI"]
            break
        if cap["format"] in cc_exts.keys():
            cc_url = cap["URI"]
            break
        print(f"No subtitle found\n{cap}")
        cap = None

    if cap:
        suffix: str = cc_exts.get(cap["format"], "")

    return (cc_url, suffix, cc_type)


def any2srt(_cc: Tuple[str, str, str],
            out_title: Path) -> None:
    """Converts any sub to srt sub
    cc from sub_check: d/l url, ext, type
    https://pycaption.readthedocs.io/en/stable/introduction.html
    """

    caps = ""
    with open(out_title.with_suffix(f".{_cc[1]}")) as _fd:
        caps = _fd.read()

    reader = detect_format(caps)
    if reader:
        with open(f"{out_title}.srt", "w") as _fe:
            _fe.write(SRTWriter().write(reader().read(caps)))

    else:
        print("No sub type found")


def sub_download(_cc: Tuple[str, str, str], out_title: Path):
    """_cc is (subtitle URL, suffix, type) from sub_check
    out_title is name of file, minus suffix"""
    try:
        sub_path = out_title.with_suffix("." + _cc[1])
        urllib.request.urlretrieve(_cc[0], str(sub_path))
        if _cc[1] != "srt":
            # Convert webvtt to srt, because
            # Kodi 19 will crash on presence of a webvtt file
            any2srt(_cc, out_title)
            # TODO remove all webvtt!
            out_title.with_suffix(f".{_cc[1]}").unlink()

    except Exception:
        print('What')
        raise  # what to do here?


def download_file(url, length, filename, rate_limit=2048):
    """rate_limit in kilobytes"""
    if length == None:
        length == 0
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
                progress_bar = "\rDownloaded: {:.2f} MB of {:.2f}".format(
                    downloaded / (1024 * 1024),
                    int(length)
                )
                sys.stdout.write(progress_bar)
                sys.stdout.flush()

    # Print a newline after the progress bar
    print()


def iter_episodes(jcontent: Dict):
    ''' Download using json file contents '''
    for item in jcontent["collections"]["episodes"]["content"]:
        show_name = item["program"]["title"]
        air_date = item["air_date"][0:10]
        ep_title = mapchars(item["title"])
        ep_title = ep_title.replace("/", "+")  # Slash be gone
        print(ep_title)

        out_dir: Path = Path(output_root, show_name)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_title: Path = Path(out_dir, f"{air_date} - {ep_title}")
        out_mp4: Path = out_title.with_suffix(".mp4")

        # Save .json
        with open(out_title.with_suffix(".json"), "w") as _fd:
            json.dump(jcontent, _fd)
        try:
            mp4 = item["mp4"]  # Video file URL
            # RESPONSE TESTING FOR CONTENTLENGTH
            req = urllib.request.Request(mp4)
            with urllib.request.urlopen(req) as response:
                content_length = response.headers["Content-Length"]
            #break
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
        sub_check_obj = sub_check(item["closedCaptions"])
        sub_download(sub_check_obj, out_title)


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
        default="daniel-tigers-neighborhood",
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
    main(args.show)
