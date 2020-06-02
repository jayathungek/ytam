from pytube import YouTube, Playlist
import time

# lorde - "https://www.youtube.com/playlist?list=PLOoPqX_q5JAUnH2ZsoTXT8nIKKKEyNVbK"

import re


def main():
    # url = "https://www.youtube.com/watch?v=t268CElxWN4"
    # url = "https://www.youtube.com/watch?v=8ATu1BiOPZA"
    # url = "https://www.youtube.com/watch?v=b_KfnGBtVeA"
    # url = "https://www.youtube.com/watch?v=iHzFbzyvEqw"
    pl_url = "https://www.youtube.com/playlist?list=PLOoPqX_q5JAUnH2ZsoTXT8nIKKKEyNVbK"
    while True:
        # video = YouTube(url)
        # print(video.title)
        # if video.title == "YouTube":
        #     return
        playlist = Playlist(pl_url)
        for url in playlist:
            try:
                print(url)
                video = YouTube(url)
                if video.title == "YouTube":
                    raise AttributeError
            except AttributeError:
                print(f"error: {url}")
                return


if __name__ == "__main__":
    # main()
    expression = re.compile(
        r"^((https:\/\/)?(www\.)?youtube\.com\/playlist\?list=(.){41})$"
    )
    result = prog.match(
        "https://www.youtube.com/playlist?list=OLAK5uy_mSKX4uUDxasnEVVBfQriUunDOnfUSNKPk"
    )
    print(result.group(0))
