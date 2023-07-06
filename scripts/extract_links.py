"""
Neuromatch Academy

Extract slide and video links from notebooks
"""
import argparse
import ast
import collections
import json
import os
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import sys

import nbformat


def bilibili_url(video_id):
    return f"https://www.bilibili.com/video/{video_id}"


def youtube_url(video_id):
    return f"https://youtube.com/watch?v={video_id}"


def osf_url(link_id):
    return f"https://osf.io/download/{link_id}"

def tutorial_order(fname):
    fname = os.path.basename(fname)
    try:
        first, last = fname.split("_")
    except ValueError:
        return (99, 99, fname)
    if first.startswith("Bonus"):
        week, day = 9, 9
    else:
        try:
            week, day = int(first[1]), int(first[3])
        except ValueError:
            week, day = 9, 9
    if last.startswith("Intro"):
        order = 0
    elif last.startswith("Tutorial"):
        order = int(last[8])
    elif last.startswith("Outro"):
        order = 10
    elif last.startswith("DaySummary"):
        order = 20
    else:
        raise ValueError(last)
    return (week, day, order)

def main(arglist):
    """Process IPython notebooks from a list of files."""
    args = parse_args(arglist)

    nb_paths = [arg for arg in args.files
                if arg.endswith(".ipynb") and
                   'student' not in arg and
                   'instructor' not in arg]
    if not nb_paths:
        print("No notebook files found")
        sys.exit(0)

    videos = collections.defaultdict(list)
    slides = collections.defaultdict(list)

    for nb_path in sorted(nb_paths, key=tutorial_order):
        # Load the notebook structure
        with open(nb_path) as f:
            nb = nbformat.read(f, nbformat.NO_CONVERT)

        # Extract components of the notebook path
        nb_dir, nb_fname = os.path.split(nb_path)
        nb_name, _ = os.path.splitext(nb_fname)

        # Loop through the cells and find video and slide ids
        for cell in nb.get("cells", []):
            for line in cell.get("source", "").split("\n"):
                l = line.strip()
                if l.startswith("video_ids = "):
                    rhs = l.split("=")[1].strip()
                    video_dict = dict(ast.literal_eval(rhs))
                    try:
                        if args.noyoutube:
                            url = bilibili_url(video_dict["Bilibili"])
                        else:
                            url = youtube_url(video_dict["Youtube"])
                    except KeyError:
                        print(f"Malformed video id in {nb_name}? '{rhs}'")
                        continue
                    if url not in videos[nb_name]:
                        videos[nb_name].append(url)
                elif l.startswith("link_id = "):
                    rhs = l.split("=")[1].strip()
                    url = osf_url(ast.literal_eval(rhs))
                    # Slides are sometimes used in multiple notebooks, so we
                    # just store the filename and the link
                    if url not in slides:
                        api_request = f"https://api.osf.io/v2/files/{ast.literal_eval(rhs)}/"
                        httprequest = Request(api_request,
                                              headers={"Accept": "application/json"})
                        try:
                            with urlopen(httprequest) as response:
                                data = json.load(response)
                                filename = data["data"]["attributes"]["name"]
                        except HTTPError as e:
                            sys.stderr.write(str(e) + "\n")
                            sys.stderr.write(f"Skipping slide {url}\n")
                            continue
                        if 'DaySummary' in nb_name:
                            filename = os.path.splitext(filename.replace("_", ""))[0] + '_DaySummary.pdf'
                        slides[url] = filename

    print(json.dumps({"videos": videos, "slides": slides}, indent=4))


def parse_args(arglist):
    """Handle the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process neuromatch tutorial notebooks"
    )
    parser.add_argument(
        "--noyoutube",
        action="store_true",
        help="Extract Bilibili links instead of youtube",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="File name(s) to process. Will filter for .ipynb extension.",
    )
    return parser.parse_args(arglist)


if __name__ == "__main__":
    main(sys.argv[1:])
