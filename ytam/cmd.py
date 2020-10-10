import os
import sys

import argparse
import colorama
from pytube import Playlist

try:
    import error
    import font
    from ytam import Downloader
except ModuleNotFoundError:
    import ytam.error as error
    import ytam.font as font
    from ytam.ytam import Downloader



full_path = os.path.realpath(__file__).split("/")
BASE = f"{'/'.join(full_path[:-1])}"


def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return ivalue

def is_affirmative(string):
    string = string.strip().lower()
    string = string.split(" ")[0]
    truthy = ["y", "yes", "true", "1", "t"]

    return string in truthy


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "url",
        metavar="URL",
        type=str,
        help="the target URL of the playlist to download",
    )
    parser.add_argument(
        "-t",
        "--titles",
        help="a plain text file containing the desired names of the songs in the playlist (each on a new line)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="the download directory (defaults to 'music' -  a subdirectory of the current directory)",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=check_positive,
        help="from which position in the playlist to start downloading (defaults to 1)",
    )
    parser.add_argument(
        "-e",
        "--end",
        type=check_positive,
        help="position in the playlist of the last song to be downloaded (defaults to last position in the playlist)",
    )
    parser.add_argument(
        "-A",
        "--album",
        type=str,
        help="the name of the album that the songs in the playlist belongs to (defaults to playlist title)",
    )
    parser.add_argument(
        "-a",
        "--artist",
        type=str,
        help="the name of the artist that performed the songs in the playlist (defaults to Unknown)",
    )
    parser.add_argument(
        "-i",
        "--image",
        type=str,
        help="the path to the image to be used as the album cover. Only works when -A flag is set",
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        help="list of proxies to use. Must be enclosed in string quotes with a space separating each proxy. Proxy format: <protocol>-<proxy>",
    )
    parser.add_argument(
        "-3",
        "--mp3",
        type=bool,
        nargs="?",
        const=True,
        default=False,
        help="converts downloaded files to mp3 format and deletes original mp4 file. Requires ffmpeg to be installed on your machine",
    )
    parser.add_argument(
        "-k",
        "--check",
        type=bool,
        nargs="?",
        const=True,
        default=False,
        help="checks whether ytam is working as it should by trying to download a pre-defined playlist and setting pre-defined metadata. Setting this argument causes ytam to ignore ALL others",
    )
    return parser.parse_args(args)

def main():
    if "--check" in sys.argv[1:] or "-k" in sys.argv[1:]:
        urls = Playlist("https://www.youtube.com/playlist?list=PLOoPqX_q5JAVPMhHjYxcUc2bxTDMyGE-a")
        playlist_title = urls.title()
        start = 0
        end = len(urls)
        album = "Test Album"
        directory = "music/"
        artist = "Test Artist"
        is_album = True
        proxies = None
        image = f"{BASE}/check/check.jpg"
        titles = f"{BASE}/check/check.txt"
        mp3 = True

    else:
        args = parse_args(sys.argv[1:])
        urls = Playlist(args.url)
        playlist_title = urls.title()
        start = 0 if args.start is None else args.start - 1
        end = len(urls) if args.end is None else args.end
        album = playlist_title if args.album is None else args.album
        directory = "music/" if args.directory is None else args.directory
        artist = "Unknown" if args.artist is None else args.artist
        is_album = False if args.album is None else True
        image = args.image 
        titles = args.titles
        mp3 = args.mp3
        
        proxies = None
        if args.proxy is not None:
            proxy_strings = [proxy.strip() for proxy in args.proxy.split(" ")]
            proxies = {}
            for proxy_string in proxy_strings:
                p = proxy_string.split('-')
                proxies[p[0]] = p[1]


    print("Initialising.")
    colorama.init()
    try:
        if start >= len(urls):
            raise error.InvalidPlaylistIndexError(start, playlist_title)
        if end < start:
            raise error.IndicesOutOfOrderError()

        downloading_message = f"Downloading songs {font.apply('gb', start+1)} - {font.apply('gb', end)} from playlist {font.apply('gb', playlist_title)}"
        text_len = len("Downloading songs ") + len(str(start)) + len(" - ") + len(str(end)) + len(" from playlist ") + len(playlist_title) 
        print(downloading_message, f"\n{font.apply('gb', '─'*text_len)}")
        d = Downloader(list(enumerate(urls[start:end])), len(urls), album, directory, artist, is_album, titles, image, proxies, mp3)
        d.start = start

        retry = True
        while retry:
            d.download()
            print(f"{font.apply('gb', '─'*text_len)}")
            print(f"{d.successful}/{len(urls[start:end])} downloaded successfully.\n")
            if len(d.retry_urls) > 0:
                d.set_retries()
                urls_copy = d.urls.copy()
                user = input(f"Retry {font.apply('fb', str(len(list(urls_copy))) + ' failed')} downloads? Y/N ")
                if not is_affirmative(user):
                    retry = False
                else:
                    print("\nRetrying.")
                    print(f"{font.apply('gb', '─'*len('Retrying.'))}")
            else:
                retry = False

        for image in d.images:
            os.remove(image)
        d.images = []

    except (
        error.InvalidPlaylistIndexError,
        error.IndicesOutOfOrderError,
        error.TitlesNotFoundError,
        error.BadTitleFormatError,
    ) as e:
        print(f"Error: {e.message}")

if __name__ == "__main__":
    main()

#https-socks5://98.162.96.41:4145
#https://18.140.249.11:80
#https://www.youtube.com/playlist?list=PLOoPqX_q5JAUSng1aEWmEC1Q4E0EJnPts
# short PL with one 10sec video: https://www.youtube.com/playlist?list=PLOoPqX_q5JAVEgR2bv8MxS9RFgxJPEoCv