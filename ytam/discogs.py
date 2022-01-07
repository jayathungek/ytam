import sys

import re
import json
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

try:
    import error
except ModuleNotFoundError:
    import ytam.error as error

ARTIST_TAG = "profile_title"
ALBUM_TAG = "section_content marketplace_box_buttons_count_1"
IMAGE_TAG = "image_gallery image_gallery_large"
TRACKLIST_TAG = "playlist"
TITLE_TAG = "tracklist_track_title"

discogs_url = r"(https?:\/\/)?(www\.)?discogs\.com\/(release|master)\/.+"
artist_exp = r".+ \(\d+\)$"

discogs_url_pattern = re.compile(discogs_url)
artist_pattern = re.compile(artist_exp)


def clean_artist(artist):
    # discogs will sometimes have a number after the artist name if they have multiple artists by that name in their
    # database. If found, delete the number

    if artist_pattern.match(artist):
        return " ".join(artist.split(" ")[:-1])
    return artist


class Discogs:
    artist: str
    image: str
    album: str
    tracks: []
    num_tracks: int

    def __init__(self, discogs_release_url):
        if not discogs_url_pattern.match(discogs_release_url):
            raise error.WrongMetadataLinkError(discogs_release_url)

        try:
            req = Request(discogs_release_url)
            req.add_header(
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/50.0.2661.102 Safari/537.36",
            )
            fp = urlopen(req)
            html_bytes = fp.read()
            fp.close()
        except Exception:
            raise error.BrokenDiscogsLinkError(discogs_release_url)

        html_str = html_bytes.decode("utf8")
        self.html = BeautifulSoup(html_str, features="html.parser")
        self.extract_image()
        self.extract_artist_album()
        self.extract_tracklist()

    def extract_image(self):
        image_json = self.html.find("div", class_=IMAGE_TAG)
        if image_json:
            image_json = image_json["data-images"]
            images = json.loads(image_json)
            highest_res = images[0]["full"]
            self.image = highest_res
        else:
            raise error.AlbumArtNotFoundError()

    def extract_artist_album(self):
        art_alb = self.html.find("h1", id=ARTIST_TAG)
        if art_alb:
            self.artist = clean_artist(art_alb.find("a").contents[0])
            self.album = art_alb.find_all("span")[-1].contents[0].strip()
        else:
            raise error.AlbumArtistNotFoundError()

    def extract_tracklist(self):
        table = self.html.find("table", class_=TRACKLIST_TAG).find_all("tr")
        if table:
            titles = []
            for track in table:
                title = track.find("span", class_=TITLE_TAG).contents[0]
                titles.append(title)

            self.tracks = titles
            self.num_tracks = len(self.tracks)
        else:
            raise error.AlbumTracklistNotFoundError()

    def make_file(self, path):
        with open(path, "w") as fh:
            num = 1
            for track in self.tracks:
                fh.write(f"{track}" if num == 1 else f"\n{track}")
                num += 1


if __name__ == "__main__":
    url = sys.argv[1]
    d = Discogs(url)
    print(d.image)
    print(f"{d.album} by {d.artist}")
    print(f"Got {len(d.tracks)} tracks:")
    for t in d.tracks:
        print(t)

    d.make_file("ytam/metadata/title.txt")
