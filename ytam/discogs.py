import sys

import re
import json
from urllib.request import Request, urlopen

try:
    import error
except ModuleNotFoundError:
    import ytam.error as error

IMAGE_TAG = "og:image"
ARTIST_TAG = "profile_title"
ALBUM_TAG = "section_content marketplace_box_buttons_count_1"
TRACKLIST_TAG = "playlist"
TITLE_TAG = "tracklist_track_title"

discogs_url = r"(https?:\/\/)?(www\.)?discogs\.com\/release\/(\d+)-.+"  # release id is stored in 3rd capture group
discogs_api_url = "https://api.discogs.com/releases"
artist_exp = r".+ \(\d+\)$"
image_exp = r"(?<=property=\"og:image\" content=\")(.+?)(?=\"(\/)?>)"
discogs_url_pattern = re.compile(discogs_url)
artist_pattern = re.compile(artist_exp)
image_pattern = re.compile(image_exp)


def clean_artist(artist):
    # discogs will sometimes have a number after the artist name if they have multiple artists by that name in their
    # database. If found, delete the number

    if artist_pattern.match(artist):
        return " ".join(artist.split(" ")[:-1])
    return artist


def extract_release_id(discogs_release_url):
    match = discogs_url_pattern.match(discogs_release_url)
    return match.groups()[2]


class Discogs:
    artist: str
    image: str
    album: str
    tracks: []
    num_tracks: int

    def __init__(self, discogs_release_url):
        if not discogs_url_pattern.match(discogs_release_url):
            raise error.WrongMetadataLinkError(discogs_release_url)

        self.extract_image(discogs_release_url)
        self.extract_metadata(extract_release_id(discogs_release_url))

    def extract_image(self, discogs_release_url):
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
        image_tag = image_pattern.findall(html_str)
        if len(image_tag) > 0:
            self.image = image_tag[0][0]
        else:
            raise error.AlbumArtNotFoundError()

    def extract_metadata(self, release_id):
        try:
            req = Request(f"{discogs_api_url}/{release_id}")
            req.add_header(
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/50.0.2661.102 Safari/537.36",
            )
            fp = urlopen(req)
            html_bytes = fp.read()
            metadata = json.loads(html_bytes.decode("utf8"))
            fp.close()
            self.artist = clean_artist(metadata["artists"][0]["name"])
            self.album = metadata["title"]
            self.tracks = [title["title"] for title in metadata["tracklist"]]
            self.num_tracks = len(self.tracks)
        except Exception:
            raise error.BrokenDiscogsLinkError(f"{discogs_api_url}/{release_id}")

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

