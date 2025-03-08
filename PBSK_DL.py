#!/usr/bin/env python3
"""Examples: 'peg-cat', 'daniel-tigers-neighborhood'"""
import sys
import urllib.request
import json
from pathlib import Path
from typing import List, Dict, Tuple
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

# TODO: rewrite as class and tuple becomes named obj variables


def sub_check(_i: List[Dict],
             cc_exts=None,
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


def jdownload(jcontent: Dict):
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
            mp4 = item["mp4"]  # URL
        except FileNotFoundError:
            print("No valid mp4!")
            raise
        # Prevent re-downloading existing mp4
        if out_mp4.is_file():
            if continuity.is_ok(out_mp4) is False:
                print('Redownloading partial download')
                out_mp4.unlink()
                urllib.request.urlretrieve(mp4, f"{out_mp4}")
        else:
            print('Downloading...')
            urllib.request.urlretrieve(mp4, f"{out_mp4}")
            try:
                continuity.is_ok(out_mp4)
            except continuity.FfmpegError as exc:
                raise continuity.FfmpegError from exc

        # Captions/Subtitles Check
        sub_check_obj = sub_check(item["closedCaptions"])
        sub_download(sub_check_obj, out_title)


def main():
    """Examples: 'peg-cat', 'daniel-tigers-neighborhood'"""
    try:
        show_name = sys.argv[1]
    except IndexError:
        show_name = "jelly-ben-pogo"
    # Retrieve show information
    urlroot = "https://content.services.pbskids.org/v2/kidspbsorg/programs/"
    with urllib.request.urlopen(urlroot + show_name) as proc:
        contents = proc.read()
    jcontent = json.loads(contents)

    ### DOWNLOAD VIDEOS ###
    jdownload(jcontent)


if __name__ == "__main__":
    main()
