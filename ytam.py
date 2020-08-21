import os
import sys
from sys import stdout
import requests

import argparse
import colorama
from pytube import YouTube, Playlist
from mutagen.mp4 import MP4, MP4Cover

import error
import font
from title import TitleGenerator


def make_safe_filename(string):
    def safe_char(c):
        if c.isalnum():
            return c
        else:
            return "_"

    return "".join(safe_char(c) for c in string).rstrip("_")

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
        help="from which position in the playlist to start downloading",
    )
    parser.add_argument(
        "-e",
        "--end",
        type=check_positive,
        help="position in the playlist of the last song to be downloaded",
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
    return parser.parse_args(args)


class Downloader:
    is_album = None
    album_image_set = False
    urls = None
    album = None
    cur_video = None
    image_filepath = None
    metadata_filepath = None
    successful = 0
    cur_song = 1
    successful_filepaths = []
    retry_urls = []

    start = None

    def __init__(self, urls, album, outdir, artist, is_album=True, metadata=None):
        self.urls = urls
        self.album = album
        self.is_album = is_album
        self.outdir = outdir
        self.artist = artist
        self.metadata_filepath = metadata
        self.images = []

    def progress_function(self, chunk, file_handle, bytes_remaining):
        title = self.cur_video.title
        size = self.cur_video.filesize
        p = ((size - bytes_remaining) * 100.0) / size
        progress = (
            f"Downloading song {font.apply('gb',str(self.cur_song))+' - '+font.apply('gb', title)} - [{p:.2f}%]"
            if p < 100
            else f"Downloading song {font.apply('gb',str(self.cur_song))+' - '+font.apply('gb', title)} - {font.apply('bl', '[Done]          ')}"
        )

        end = "\n" if p == 100 else "\r"

        print(progress, end=end, flush=True)

    def apply_metadata(
        self, track_num, total, path, album, title, artist, image_filename
    ):
        song = MP4(path)
        song["\xa9alb"] = album
        song["\xa9nam"] = title
        song["\xa9ART"] = artist
        song["trkn"] = [(track_num, total)]

        with open(image_filename, "rb") as f:
            song["covr"] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]
        song.save()

    @staticmethod
    def write_image(url, index, outdir):
        thumbnail_image = requests.get(url)
        filename = outdir + f"album_art_{str(index)}.jpg"
        with open(filename, "wb",) as f:
            f.write(thumbnail_image.content)
        return filename

    def download(self):
        metadata = None
        if self.metadata_filepath is not None:
            tg = TitleGenerator(self.metadata_filepath, self.artist)
            tg.make_titles()
            metadata = tg.get_titles()

        for num, url in enumerate(self.urls):
            yt = None
            self.cur_song = num+self.start+1
            try:
                yt = YouTube(url)
            except:
                self.retry_urls.append(url)
                print(
                    f"Downloading song {font.apply('gb', str(self.cur_song))} - {font.apply('bf', '[Failed]         ')}\n"
                )
                continue

            path = None
            try:
                yt.register_on_progress_callback(self.progress_function)
                self.cur_video = (
                    yt.streams.filter(type="audio", subtype="mp4")
                    .order_by("abr")
                    .desc()
                    .first()
                )
                path = self.cur_video.download(
                    output_path=self.outdir,
                    filename=make_safe_filename(self.cur_video.title),
                )
                self.successful_filepaths.append(path)
                self.successful += 1
            except:
                self.retry_urls.append(url)
                print(
                    f"Downloading song {font.apply('gb',str(self.cur_song))+' - '+font.apply('gb', self.cur_video.title)} - {font.apply('bf', '[Failed]         ')}\n"
                )
                continue

            if self.is_album:
                if not self.album_image_set:
                    image_path = Downloader.write_image(
                        yt.thumbnail_url, num, self.outdir
                    )
                    self.images.append(image_path)
                    self.image_filepath = image_path
                    self.album_image_set = True
            else:
                image_path = Downloader.write_image(yt.thumbnail_url, num, self.outdir)
                self.images.append(image_path)
                self.image_filepath = image_path

            track_title = None
            track_artist = None
            if metadata is not None:
                t = metadata[num]
                track_title = t.title if not t.unused else self.cur_video.title
                track_artist = t.artist if not t.unused else self.artist
            else:
                track_title = self.cur_video.title
                track_artist = self.artist

            try:
                self.apply_metadata(
                    num + 1,
                    len(self.urls),
                    path,
                    self.album,
                    track_title,
                    track_artist,
                    self.image_filepath,
                )
                print(f"└── Applying metadata - {font.apply('bl', '[Done]')}\n")

            except:
                print(f"└── Applying metadata - {font.apply('bf', '[Failed]')}\n")

        for image in self.images:
            os.remove(image)
        self.images = []

    def set_retries(self):
        self.album_image_set = False
        self.urls = self.retry_urls
        self.retry_urls = []


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    print("Initialising.")
    colorama.init()
    urls = Playlist(args.url)
    playlist_title = urls.title()

    start = 0 if args.start is None else args.start - 1
    end = len(urls) if args.end is None else args.end
    album = playlist_title if args.album is None else args.album
    directory = "music/" if args.directory is None else args.directory
    artist = "Unknown" if args.artist is None else args.artist
    is_album = False if args.album is None else True

    try:
        if start >= len(urls):
            raise error.InvalidPlaylistIndexError(start, playlist_title)
        if end < start:
            raise error.IndicesOutOfOrderError()

        downloading_message = f"Downloading songs {font.apply('gb', start+1)} - {font.apply('gb', end)} from playlist {font.apply('gb', playlist_title)}"
        text_len = len("Downloading songs ") + len(str(start)) + len(" - ") + len(str(end)) + len(" from playlist ") + len(playlist_title) 
        print(downloading_message, f"\n{font.apply('gb', '─'*text_len)}")
        d = Downloader(urls[start:end], album, directory, artist, is_album, args.titles)
        d.start = start

        retry = True
        while retry:
            d.download()
            print(f"{font.apply('gb', '─'*text_len)}")
            print(f"{d.successful}/{len(urls[start:end])} downloaded successfully.\n")
            if len(d.retry_urls) > 0:
                d.set_retries()
                user = input(f"Retry {font.apply('fb', str(len(d.urls)) + ' failed')} downloads? Y/N ")
                if not is_affirmative(user):
                    retry = False
                else:
                    print("\nRetrying.")
                    print(f"{font.apply('gb', '─'*len('Retrying.'))}")
            else:
                retry = False

    except (
        error.InvalidPlaylistIndexError,
        error.IndicesOutOfOrderError,
        error.TitlesNotFoundError,
        error.BadTitleFormatError,
    ) as e:
        print(f"Error: {e.message}")


# Downloading Lorde - Tennis Court - [100.0%]
# Downloading Lorde - Tennis Court - [Done]