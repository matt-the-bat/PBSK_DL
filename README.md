# PBSK_DL
Download the freely available videos on PBSKids.org

# Installation
`ffmpeg` is required, to check for partial file downloads

`pip install -r requirements.txt`

`urllib3` for requests
PBS's own `pycaption` module is needed to convert subs to SRT format.

# Usage
Pass the show name, as an argument. Must be lowercase, with hyphens in place of spaces.
If no argument, show defaults to daniel-tigers-neighborhood!

# Changes 
- All prompting has been removed.
- Script now only downloads episodes, and not clips.
- Downloads subtitles, ensuring SRT type is created.
