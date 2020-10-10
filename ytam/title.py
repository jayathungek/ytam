import os
import re
try:
    import error
except ModuleNotFoundError:
    import ytam.error as error

DELIM = "<@>"

class Title:
    def __init__(self, index, title, artist):
        self.unused = False
        self.index = index
        self.title = title
        self.artist = artist


class TitleGenerator:
    def __init__(self, filename, artist):
        self.filename = filename
        self.artist = artist
        self.titles = []

    def check_line(self, line, line_num):
        if not (len(line) > 0 and len(line) < 3):
            msg = "wrong number of fields - only title and artist allowed"
            raise error.BadTitleFormatError(self.filename, line_num + 1, msg)

    def make_titles(self):
        try:
            with open(self.filename, "r") as f:
                lines = f.readlines()

                for i, line in enumerate(lines):
                    line = line.strip()
                    line = re.split(DELIM, line)
                    self.check_line(line, i)

                    t = Title(i, None, None)
                    if line[0] == "":
                        t.unused = True

                    if len(line) == 1:
                        t.title = line[0].strip()
                        t.artist = self.artist.strip()
                    elif len(line) == 2:
                        t.title = line[0].strip()
                        t.artist = line[1].strip()
                    self.titles.append(t)
        except FileNotFoundError:
            raise error.TitlesNotFoundError(self.filename)

    def get_titles(self):
        return self.titles


if __name__ == "__main__":
    t = TitleGenerator("./titles.txt", "Cool Artist")
    t.make_titles()
    ts = t.get_titles()

    for t in ts:
        print(
            f"{t.index}: {t.title}, {t.artist} - {('un' if t.unused else '' )+ 'used'}"
        )
