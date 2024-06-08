#!/usr/bin/env python
import sys
import urllib.request
import json
from pathlib import Path
from pycaption import (  # type: ignore
    CaptionConverter,
    detect_format,
    SAMIReader,
    DFXPReader,
    WebVTTReader,
    SRTWriter,
)
from typing import List, Dict, Tuple
import continuity
import time
import argparse
from rich import print as print


output_root = Path.cwd()
# output_root = Path.home()


def mapchars(x: str) -> str:
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
    for k, v in charmap.items():
        x = x.replace(k, v)
    return x


# TODO rewrite as class and tuple becomes named obj variables


def subCheck(
    _i: List[Dict],
    ccExts: Dict = {
        "SRT": "srt",
        "WebVTT": "vtt",
        "DFXP": "dfxp",
        "Caption-SAMI": "sami",
    },
) -> Tuple[str, str, str]:  # url, ext, type
    """Captions/Subtitles Check
    Returns EXT/subtitletype ?"""
    for cap in _i:
        ccType = cap["format"]
        ccURL = ""
        if "SRT" in ccType:
            ccURL = cap["URI"]
            break
        elif cap["format"] in ccExts.keys():
            ccURL = cap["URI"]
            break
        else:
            print(f"No subtitle found\n{cap}")

    suffix: str = ccExts.get(cap["format"], "")
    return (ccURL, suffix, ccType)


def any2srt(cc: Tuple[str, str, str], out_title: Path) -> None:
    """Converts any sub to srt sub
    cc from subCheck: d/l url, ext, type
    https://pycaption.readthedocs.io/en/stable/introduction.html
    """

    caps = ""
    with open(out_title.with_suffix(f".{cc[1]}")) as fd:
        caps = fd.read()

    reader = detect_format(caps)
    if reader:
        with open(f"{out_title}.srt", "w") as fe:
            fe.write(SRTWriter().write(reader().read(caps)))

    else:
        print("No sub type found")


def subDownload(cc: Tuple[str, str, str], out_title: Path):
    """cc is (subtitle URL, suffix, type) from subCheck
    out_title is name of file, minus suffix"""
    try:
        sub_Path = out_title.with_suffix("." + cc[1])
        urllib.request.urlretrieve(cc[0], str(sub_Path))
        if cc[1] != "srt":
            """Convert webvtt to srt, because
            Kodi 19 will crash on presence of a webvtt file
            """
            any2srt(cc, out_title)
            # TODO remove all webvtt!
            out_title.with_suffix(f".{cc[1]}").unlink()

    except Exception:
        raise  # what to do here?


def download_file(url, filename, rate_limit=2048):
    """rate_limit in kilobytes"""
    start_time = time.time()
    rate_limit = rate_limit * 1024
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        downloaded = 0

        with open(filename, "wb") as file:
            while True:
                chunk = response.read(1024)
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
                progress_bar = "\rDownloaded: {:.2f} MB".format(
                    downloaded / (1024 * 1024)
                )
                sys.stdout.write(progress_bar)
                sys.stdout.flush()

    # Print a newline after the progress bar
    print()


def iter_episodes(jcontent: Dict):
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

        """ Save .json """
        with open(out_title.with_suffix(".json"), "w") as fd:
            json.dump(jcontent, fd)
        try:
            mp4 = item["mp4"]  # Video file URL
            # RESPONSE TESTING FOR CONTENTLENGTH
            req = urllib.request.Request(mp4)
            with urllib.request.urlopen(req) as response:
                print(response.headers["Content-Length"])
            break
            # END RESPONSE TESTING
        except FileNotFoundError:
            print("No valid mp4!")
            raise
        # Prevent re-downloading existing mp4
        if out_mp4.is_file():
            if continuity.is_ok(out_mp4) is False:
                print("Redownloading partial download")
                out_mp4.unlink()
                download_file(mp4, f"{out_mp4}")
        else:
            print("Downloading...")

            download_file(mp4, f"{out_mp4}")
            try:
                continuity.is_ok(out_mp4)
            except continuity.ffmpegError:
                raise continuity.ffmpegError

        # Captions/Subtitles Check
        subDownload(subCheck(item["closedCaptions"]), out_title)


def main():
    urlroot = "https://content.services.pbskids.org/v2/kidspbsorg/programs/"
    contents = urllib.request.urlopen(urlroot + args.show).read()
    jcontent = json.loads(contents)
    """ DOWNLOAD VIDEOS """

    iter_episodes(jcontent)


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
        default=1024 * 1024,
        help="Rate limit in bytes per second (default: 1 MB/s)",
    )
    args = parser.parse_args()

    main()
