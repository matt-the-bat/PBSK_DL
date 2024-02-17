#!/usr/bin/env python
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from pycaption import (CaptionConverter, DFXPReader, SAMIReader, SRTWriter,
                       WebVTTReader, detect_format)
from rich.progress import track

output_root = Path().cwd()
url_root = "https://content.services.pbskids.org/v2/kidspbsorg/"


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


def any2srt(cc: Tuple[str, str, str], out_title: Path):
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
        # urllib.request.urlretrieve(cc[0], str(sub_Path))
        response = requests.get(cc[0]).content
        if cc[1] != "srt":
            """Convert webvtt to srt, because
            Kodi 19 will crash on presence of a webvtt file
            """
            any2srt(cc, out_title)
            # TODO remove all webvtt!
            out_title.with_suffix(f".{cc[1]}").unlink()

    except Exception:
        raise  # what to do here?


def jdownload(jcontent: Dict):
    print("Downloading...")
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
            mp4 = item["mp4"]  # URL
            # Prevent re-downloading existing mp4
            if not out_mp4.is_file():
                response = requests.get(mp4, f"{out_mp4}", stream=True)

                total_size = int(response.headers.get("content-length", 0))
                block_size = 1024
                chunks = response.iter_content(chunk_size=block_size)

                with open(out_mp4, "wb") as file:
                    with track(
                        total=total_size,
                        transient=True,
                        description="Downloading...",
                    ) as progress_bar:
                        for chunk in track(
                            chunks
                        ):  # Track the chunks as the sequence
                            if chunk:  # Filter out keep-alive new chunks
                                file.write(chunk)
                                progress_bar.update(len(chunk))

                if total_size != 0 and progress_bar.completed != total_size:
                    raise RuntimeError("Could not download file")

        except Exception:
            print("No valid mp4!")
            raise
        # Captions/Subtitles Check
        subDownload(subCheck(item["closedCaptions"]), out_title)


def main():
    """Examples: 'peg-cat', 'daniel-tigers-neighborhood'"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "show_name",
        default="daniel-tigers-neighborhood",
        nargs="?",
        help="The name of the show",
    )

    args = parser.parse_args()

    if args.show_name:
        show_name = args.show_name
        url_Progs = url_root + "programs/"
        jcontent = requests.get(url_Progs + show_name).json()

        """ DOWNLOAD VIDEOS """
        """from rich import print

        print(f"{url_root= }\n{show_name= }")
        print(jcontent)"""
        jdownload(jcontent)

    elif args.list:
        """Query list of shows"""
        url_home = url_root + "home/"
    # Query


if __name__ == "__main__":
    main()
