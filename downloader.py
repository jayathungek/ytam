from pytube import YouTube, Playlist
import os, sys
import argparse
import requests
from mutagen.mp4 import MP4, MP4Cover
from multiprocessing import Process, Event, Value, Queue
from multiprocessing.pool import ThreadPool, Pool
from threading import Thread
import random, time

from title import TitleGenerator

# music - "https://www.youtube.com/playlist?list=PLOoPqX_q5JAUWBWlqVs4faV4Y3b0ejvhv"
# lorde - "https://www.youtube.com/playlist?list=PLOoPqX_q5JAUnH2ZsoTXT8nIKKKEyNVbK"
# sdmsc - "https://www.youtube.com/playlist?list=PLOoPqX_q5JAVfmDexA-05pwSoIDdrjveE"


def make_safe_filename(string):
    def safe_char(c):
        if c.isalnum():
            return c
        else:
            return "_"

    return "".join(safe_char(c) for c in string).rstrip("_")


def is_affirmative(string):
    string = string.strip().lower()
    string = string.split(" ")[0]
    truthy = ["y", "yes", "true", "1", "t"]

    return string in truthy


class YTDL:
    def __init__(self):
        self.to_download = []
        self.downloaded_songs = []
        self.retry_songs = []
        self.num_total = 0
        self.num_tracks = 0
        self.is_album = True
        self.has_album_art = False

        self.title_list = []

        self.done = Event()
        self.done.set()
        self.init = Event()
        self.can_download = Event()
        self.re_download = Event()

        self.download_t = None
        self.init_t = None
        self.download_q = None
        self.testflag = ""
        self.running = True
        self.count = 0

    def reset(self):
        self.thumbnail_url = None
        self.to_download = []
        self.downloaded_songs = []
        self.retry_songs = []
        self.num_total = 0
        self.num_tracks = 0
        self.has_album_art = False

        self.download_t = None
        self.init_t = None
        self.done = Event()
        self.done.set()
        self.init = Event()
        self.can_download = Event()

    def pass_params(
        self, url, album, artist, title_list, directory, start_at, end_at, download_q
    ):
        self.download_q = download_q
        self.url = url
        self.start_at = start_at
        self.end_at = end_at
        self.album = album
        self.artist = "Unknown" if artist == None else artist
        self.title_list = title_list
        self.directory = "./" if directory == None else directory

    def init_playlist(self):
        playlist = Playlist(self.url)
        title = playlist.title()
        self.playlist_title = title
        if self.album == None:
            self.is_album = False
            self.album = playlist.title()
        self.num_total = len(playlist)
        self.playlist = playlist[self.start_at : self.end_at + 1]
        self.num_tracks = len(self.playlist)

        msg_num_total = {
            "text": "Added total number of songs.",
            "value": self.num_total,
        }
        msg_album = {"text": "Added album name.", "value": self.album}
        msg_num_tracks = {
            "text": "Added selected number of songs.",
            "value": self.num_tracks,
        }
        msg_done = {"text": "Added all playlist metadata.", "value": None}
        self.download_q.put(("OK_IM", msg_num_total))
        self.download_q.put(("OK_IM", msg_album))
        self.download_q.put(("OK_IM", msg_num_tracks))
        self.download_q.put(("OK_IN", msg_done))

    def init_download(self, download_indices=None):
        if download_indices is None:
            download_indices = [i for i in range(self.num_tracks)]
        else:
            self.testflag = "retrying " + str(len(download_indices)) + " songs"

        self.to_download = []
        self.downloaded_songs = []
        self.retry_songs = []

        init_dl_msg = {"text": None}

        for num, url in enumerate(self.playlist):
            video = None
            try:
                video = YouTube(url)
                if video is None:
                    raise AttributeError
            except AttributeError:
                init_dl_msg["text"] = "internal"
                init_dl_msg["num"] = num + 1
                init_dl_msg["url"] = url
                self.download_q.put(("INPUT", init_dl_msg))
                break

            streams = video.streams.filter(type="audio", subtype="mp4").order_by("abr")
            if len(streams) == 0:
                no_stream_msg = {}
                no_stream_msg[
                    "text"
                ] = f"No audio streams of type audio/mp4 found for {video.title}."
                self.download_q.put(("ERR", no_stream_msg))
                # print('No audio streams of type audio/mp4 found for {}.'.format(video.title))
                pass
            else:
                song = streams[-1]
                song_data = {}
                song_data["song"] = song
                song_data["title"] = video.title
                self.testflag = video.title
                song_data["track_num"] = [(num + 1, self.num_tracks)]
                song_data["index"] = num
                song_data["thumbnail_url"] = video.thumbnail_url
                if num in download_indices:
                    self.to_download.append(song_data)

        self.testflag = "dl init ok"

    def download(self):
        curr_num = 1
        for song_data in self.to_download:
            song = song_data["song"]
            downloading_msg = {"text": None, "arg": curr_num}
            try:
                if self.is_stopped():
                    return
                downloading_msg["text"] = f"Downloading {song.title} ..."
                self.download_q.put(("DL", downloading_msg))
                # print('downloading {}'.format(song.title))
                # if random.random() < 0.45:
                #     raise Exception()
                self.testflag = f"started downloading song {curr_num}"
                path = song.download(
                    output_path=self.directory, filename=make_safe_filename(song.title)
                )
                song_data["path"] = path
                self.downloaded_songs.append(song_data)
                downloading_msg["text"] = f"Downloading {song.title} ... ok."
                self.download_q.put(("OK_DL", downloading_msg))
            except:
                # print('could not download {}'.format(song.title))
                downloading_msg["text"] = f"Downloading {song.title} ... failed."
                self.download_q.put(("ERR_DL", downloading_msg))
                self.retry_songs.append(song_data)
            finally:
                curr_num += 1

        download_complete_msg = {"text": "Download complete."}
        self.download_q.put(("END_DL", download_complete_msg))

    def set_metadata(self):
        if self.is_stopped():
            return
        if len(self.downloaded_songs) == 0:
            return

        art_to_remove = []
        for song_data in self.downloaded_songs:
            if self.is_stopped():
                return

            if not self.is_album:
                album_art_msg = {
                    "text": f"Downloading album art for {song_data['title']}..."
                }
                try:
                    self.download_q.put(("AA", album_art_msg))
                    thumbnail_image = requests.get(song_data["thumbnail_url"])
                    with open(
                        self.directory + f"album_art_{str(song_data['index'])}.jpg",
                        "wb",
                    ) as f:
                        f.write(thumbnail_image.content)
                    album_art_msg[
                        "text"
                    ] = f"Downloading album art for {song_data['title']}... ok."
                    self.download_q.put(("OK_AA", album_art_msg))
                except:
                    album_art_msg[
                        "text"
                    ] = f"Downloading album art for {song_data['title']}... failed."
                    self.download_q.put(("ERR_AA", album_art_msg))

            elif not self.has_album_art:
                album_art_msg = {
                    "text": f"Downloading album art for {song_data['title']}..."
                }
                try:
                    self.download_q.put(("AA", album_art_msg))
                    thumbnail_image = requests.get(song_data["thumbnail_url"])
                    with open(
                        self.directory + f"album_art_{str(song_data['index'])}.jpg",
                        "wb",
                    ) as f:
                        f.write(thumbnail_image.content)
                    self.download_q.put(("OK_AA", album_art_msg))
                    self.has_album_art = True
                except:
                    album_art_msg[
                        "text"
                    ] = f"Downloading album art for {song_data['title']}... failed."
                    self.download_q.put(("ERR_AA", album_art_msg))

            metadata_msg = {}
            metadata_msg["text"] = f"Setting metadata for {song_data['title']} ..."
            self.download_q.put(("MD", metadata_msg))

            # print('setting metadata for {}'.format(song_data['title']))
            if self.is_album:
                filename = self.directory + "album_art_0.jpg"
            else:
                filename = self.directory + f"album_art_{str(song_data['index'])}.jpg"

            song_title = None
            song_artist = None
            song_index = song_data["index"]
            try:
                t = self.title_list[song_index]
                if not t.unused:
                    song_title = t.title
                    song_artist = t.artist
                else:
                    song_title = song_data["title"]
                    song_artist = self.artist
            except IndexError:
                song_title = song_data["title"]
                song_artist = self.artist

            try:
                song = MP4(song_data["path"])
                song["\xa9alb"] = self.album
                song["\xa9nam"] = song_title
                song["\xa9ART"] = song_artist
                song["trkn"] = song_data["track_num"]

                with open(filename, "rb") as f:
                    song["covr"] = [
                        MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)
                    ]
                song.save()
                metadata_msg[
                    "text"
                ] = f"Setting metadata for {song_data['title']} ... ok."
                # self.testflag = metadata_msg["text"]
                self.download_q.put(("OK_MD", metadata_msg))
            except Exception as e:
                metadata_msg[
                    "text"
                ] = f"Setting metadata for {song_data['title']} ... failed."
                self.download_q.put(("ERR_MD", metadata_msg))
            finally:
                art_to_remove.append(filename)

        metadata_complete_msg = {}
        metadata_complete_msg["text"] = "Finished setting metadata."
        self.download_q.put(("END_MD", metadata_complete_msg))
        for filename in art_to_remove:
            try:
                os.remove(filename)
            except OSError:
                pass

    def retry_init(self):
        ok = input(
            f"{self.num_total} songs found in playlist {self.playlist_title}. Is this correct? (Y - yes, download/ N - no, retry) "
        )
        if not is_affirmative(ok):
            print("retrying...")
            self.init_playlist()
            return True
        else:
            print("playlist ok.")
            return False

    def retry_download(self):
        ok = input(
            f"{len(self.retry_songs)} songs failed to download. Try downloading them again? (Y/N) "
        )
        if is_affirmative(ok):
            print("retrying failed songs...")
            self.init_download([song_data["index"] for song_data in self.retry_songs])
            self.download()
            return True
        else:
            print("skip failed songs.")
            return False

    def ext_download(self):
        if len(self.retry_songs) > 0:
            self.init_download([song_data["index"] for song_data in self.retry_songs])
        else:
            self.init_download()
        self.download()
        self.set_metadata()
        if len(self.retry_songs) > 0:
            msg = {}
            msg["text"] = "retry"
            msg["num"] = len(self.retry_songs)
            self.download_q.put(("INPUT", msg))

    def has_retries(self):
        return len(self.retry_songs) > 0

    def main_loop(self):
        # if not self.ext:
        #   retry_init = True
        #   while retry_init:
        #       retry_init = self.retry_init()

        #   self.init_download()
        #   self.download()
        #   self.set_metadata()

        #   retry_download = True
        #   successfully_downloaded = len(self.downloaded_songs)
        #   while retry_download and len(self.retry_songs) > 0:
        #       retry_download = self.retry_download()
        #       if retry_download:
        #           self.set_metadata()
        #           successfully_downloaded += len(self.downloaded_songs)

        #   print('processed {downloaded}/{total} songs successfully.'.format(downloaded=successfully_downloaded, total=self.num_tracks))
        # else:
        # self.done.clear()
        # self.init.clear()
        # self.can_download.clear()
        while self.running:
            if self.init.is_set():
                self.init.clear()
                self.testflag = "in init"
                self.init_t = Thread(target=self.init_playlist)
                self.init_t.setDaemon(True)
                self.init_t.start()

            if self.can_download.is_set():
                self.can_download.clear()
                self.testflag = "dl started"
                self.download_t = Thread(target=self.ext_download)
                self.download_t.setDaemon(True)
                self.download_t.start()

            # if self.re_download.is_set():
            #     self.testflag = "re dl started"
            #     # successfully_downloaded = len(self.downloaded_songs)
            #     # successfully_downloaded += len(self.downloaded_songs)
            #     self.re_download_t = Thread(target=self.ext_download)
            #     self.re_download_t.setDaemon(True)
            #     self.re_download_t.start()
            #     self.re_download.clear()

            self.count += 1

    def stop(self):
        self.running = False
        msg = {"text": "Downloader stopped."}
        if self.download_q is not None:
            self.download_q.put(("STOP", msg))

    def start(self):
        self.running = True
        # self.main_loop()

    def is_stopped(self):
        return not self.running

    def set_init(self):
        self.init.set()

    def set_re_init(self):
        self.re_init.set()

    def set_can_download(self):
        self.can_download.set()

    def set_re_download(self):
        self.re_download.set()


# def parse_args(args):
#     parser = argparse.ArgumentParser()
#     parser.add_argument(
#         "url",
#         metavar="URL",
#         type=str,
#         help="the target URL of the playlist to download",
#     )
#     parser.add_argument(
#         "-t",
#         "--titles",
#         help="a plain text file containing the desired names of the songs in the playlist (each on a new line)",
#     )
#     parser.add_argument(
#         "-d",
#         "--directory",
#         help="the download directory (defaults to current directory)",
#     )
#     parser.add_argument(
#         "-s",
#         "--start",
#         type=int,
#         help="from which position in the playlist to start downloading (indexed from, and defaults to 0)",
#     )
#     parser.add_argument(
#         "-A",
#         "--album",
#         type=str,
#         help="the name of the album that the songs in the playlist belongs to (defaults to playlist title)",
#     )
#     parser.add_argument(
#         "-a",
#         "--artist",
#         type=str,
#         help="the name of the artist that performed the songs in the playlist (defaults to Unknown)",
#     )
#     return parser.parse_args(args)


# if __name__ == '__main__':
#   args = parse_args(sys.argv[1:])
#   ytdl = YTDL(args.url, args.album, args.artist, args.titles, args.directory, args.start)
#   ytdl.start()

# retry_init = True
# while retry_init:
#   retry_init = ytdl.retry_init()

# ytdl.init_download()
# ytdl.download()
# ytdl.set_metadata()

# retry_download = True
# successfully_downloaded = len(ytdl.downloaded_songs)
# while retry_download and len(ytdl.retry_songs) > 0:
#   retry_download = ytdl.retry_download()
#   if retry_download:
#       ytdl.set_metadata()
#       successfully_downloaded += len(ytdl.downloaded_songs)

# print('processed {downloaded}/{total} songs successfully.'.format(downloaded=successfully_downloaded, total=ytdl.num_tracks))
