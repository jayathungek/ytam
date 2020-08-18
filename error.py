class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class EmptyUrlFieldError(Error):
    def __init__(self):
        self.message = "URL field cannot be empty."


class InvalidUrlError(Error):
    def __init__(self, url):
        self.message = f"URL {url} is not a valid YouTube playlist link."


class InvalidPlaylistError(Error):
    def __init__(self):
        self.message = "Playlist is invalid."


class TitlesNotFoundError(Error):
    def __init__(self, filename):
        self.message = f"TIL file {filename} not found."


class BadTitleFormatError(Error):
    def __init__(self, filename, line, msg):
        self.message = f"Bad formatting on line {line} of {filename}: {msg}."


class InvalidPlaylistIndexError(Error):
    def __init__(self, index, title):
        self.message = f"Start index {index} is out of range for playlist {title}."


class IndicesOutOfOrderError(Error):
    def __init__(self):
        self.message = f"End index must be greater that start index."


class InvalidFieldError(Error):
    def __init__(self, field, msg):
        self.message = f"Invalid argument for field {field} - {msg}."


class InvalidPathError(Error):
    def __init__(self, path):
        self.message = f"DIR {path} is not a valid directory."


# bad url
# url not for playlist
# title file not found
# invalid line in title file
# directory not found
