import os 
import requests
import asyncio

from pytube import YouTube, Playlist
from mutagen.mp4 import MP4, MP4Cover

from ffmpeg import FFmpeg

try:
    import font
    from title import TitleGenerator
except ModuleNotFoundError:
    import ytam.font as font
    from ytam.title import TitleGenerator


def make_safe_filename(string):
    def safe_char(c):
        if c.isalnum():
            return c
        else:
            return "_"

    return "".join(safe_char(c) for c in string).rstrip("_")

def extract_title(string):
    return string.split(".")[0]

def extract_ext(string):
    return string.split(".")[1]

def to_sec(timestamp):
    sep = timestamp.split(":")
    h, m, s = (int(sep[0]), int(sep[1]), float(sep[2]))
    return (h * 60 * 60) + (m * 60) + round(s)

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

    def __init__(self, urls, total_songs, album, outdir, artist, is_album, metadata, image_filepath, proxies, mp3):
        self.urls = urls
        self.total_songs = total_songs
        self.album = album
        self.is_album = is_album
        self.outdir = outdir
        self.artist = artist
        self.metadata_filepath = metadata
        self.image_filepath = image_filepath
        self.images = []
        self.proxies = proxies
        self.mp3 = mp3


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

        if image_filename is not None:
            with open(image_filename, "rb") as f:
                song["covr"] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]
        
        song.save()
        

    @staticmethod
    def download_image(url, index, outdir):
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

        loop = asyncio.get_event_loop()
        for num, url in self.urls:
            yt = None
            self.cur_song = num+self.start+1
            try:
                if self.proxies is not None:
                    yt = YouTube(url, proxies=self.proxies)
                else:
                    yt = YouTube(url)

            except Exception as e:
                self.retry_urls.append((num, url))
                print(
                    f"Downloading song {font.apply('gb', str(self.cur_song))} - {font.apply('bf', '[Failed - ')} {font.apply('bf', str(e) + ']')}\n"
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
                
                safe_name = extract_title(make_safe_filename(self.cur_video.title))
                path = self.cur_video.download(
                    output_path=self.outdir,
                    filename=safe_name,
                )
                self.successful_filepaths.append(path)
                self.successful += 1
            except Exception as e:
                self.retry_urls.append((num, url))
                print(
                    f"Downloading song {font.apply('gb',str(self.cur_song))+' - '+font.apply('gb', self.cur_video.title)} - {font.apply('bf', '[Failed - ')} {font.apply('bf', str(e) + ']')}\n"
                )

                continue

            # if self.is_album:
            #     if self.image_filepath is None:
            #         if not self.album_image_set:
            #             image_path = Downloader.download_image(
            #                 yt.thumbnail_url, num, self.outdir
            #             )
            #             self.images.append(image_path)
            #             self.image_filepath = image_path
            #             self.album_image_set = True
            # else:
            #     image_path = Downloader.download_image(yt.thumbnail_url, num, self.outdir)
            #     self.images.append(image_path)
            #     self.image_filepath = image_path

            track_title = None
            track_artist = None
            if metadata is not None:
                t = metadata[num]
                track_title = t.title if not t.unused else self.cur_video.title
                track_artist = t.artist if not t.unused else self.artist
            else:
                track_title = self.cur_video.title
                track_artist = self.artist

            metadata_branch = "├──" if self.mp3 else "└──"

            try:
                self.apply_metadata(
                    num + 1,
                    self.total_songs,
                    path,
                    self.album,
                    track_title,
                    track_artist,
                    self.image_filepath
                )
                print(f"{metadata_branch} Applying metadata - {font.apply('bl', '[Done]')}")

            except Exception as e:
                print(f"{metadata_branch} Applying metadata - {font.apply('bf', '[Failed - ')} {font.apply('bf', str(e) + ']')}")
            
            if self.mp3:
                ffmpeg = FFmpeg().input(path).output(f"{extract_title(path)}.mp3")

                @ffmpeg.on('progress')
                def mp3_conv_progress(event):
                    p = (to_sec(event.time)/int(yt.length)) * 100 
                    progress = (
                        f"└── Converting to mp3 - [{p:.2f}%]"
                        if p < 100
                        else f"└── Converting to mp3 - {font.apply('bl', '[Done]          ')}"
                    )

                    end = "\n" if p >= 100 else "\r"
                    print(progress, end=end, flush=True)

                try:
                    loop.run_until_complete(ffmpeg.execute())

                    os.remove(f"{extract_title(path)}.mp4")
                    path = f"{extract_title(path)}.mp3"
                
                except Exception as e:
                    print(f"└── Converting to mp3 - {font.apply('bf', '[Failed - ')} {font.apply('bf', str(e) + ']')}")

            print(" ")
        loop.close()





    def set_retries(self):
        self.album_image_set = False
        self.urls = self.retry_urls
        self.retry_urls = []