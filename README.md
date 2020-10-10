# ytam - YouTube Album Maker

A commandline utility that enables the creation of albums from Youtube playlists.

## Getting Started

<!--These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system. -->

### Prerequisites

To be able to use the mp4 to mp3 conversion feature, ffmpeg must be installed.

#### Debian:

```
sudo apt-get install ffmpeg
```

#### Windows:

- Download ffmpeg binaries [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.zip)
- Add the bin\\ directory to Windows PATH
 
### Installing
ytam depends on a specific patch of pytube, which is not yet incorporated into its official release. Until this happens, first install the patch using:

```
pip install git+git://github.com/nficano/pytube.git@0f32241c89192b22de9cfbfee1303a1bcee18bd3
```

Then:

```
pip install ytam
```

Usage:

```
usage: ytam [-h] [-t TITLES] [-d DIRECTORY] [-s START] [-e END] [-A ALBUM]
            [-a ARTIST] [-i IMAGE] [-p PROXY] [-3 [MP3]]
            URL

positional arguments:
  URL                   the target URL of the playlist to download

optional arguments:
  -h, --help            show this help message and exit
  -t TITLES, --titles TITLES
                        a plain text file containing the desired names of the
                        songs in the playlist (each on a new line)
  -d DIRECTORY, --directory DIRECTORY
                        the download directory (defaults to 'music' - a
                        subdirectory of the current directory)
  -s START, --start START
                        from which position in the playlist to start
                        downloading
  -e END, --end END     position in the playlist of the last song to be
                        downloaded
  -A ALBUM, --album ALBUM
                        the name of the album that the songs in the playlist
                        belongs to (defaults to playlist title)
  -a ARTIST, --artist ARTIST
                        the name of the artist that performed the songs in the
                        playlist (defaults to Unknown)
  -i IMAGE, --image IMAGE
                        the path to the image to be used as the album cover.
                        Only works when -A flag is set
  -p PROXY, --proxy PROXY
                        list of proxies to use. Must be enclosed in string
                        quotes with a space separating each proxy. Proxy
                        format: <protocol>-<proxy>
  -3 [MP3], --mp3 [MP3]
                        converts downloaded files to mp3 format and deletes
                        original mp4 file. Requires ffmpeg to be installed on
                        your machine
  -k [CHECK], --check [CHECK]
                        checks whether ytam is working as it should by trying
                        to download a pre-defined playlist and setting pre-
                        defined metadata. Setting this argument causes ytam to
                        ignore ALL others
```

## Tests
TODO
<!-- ## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system -->

## Built With

* [pytube](http://github.com/nficano/pytube.git) - Lightweight Python library for downloading videos
* [mutagen](https://mutagen.readthedocs.io/en/latest/api/mp4.html) - For MP4 metadata tagging
* [argparse](https://docs.python.org/3/library/argparse.html) - For parsing commandline arguments
* [ffmpeg](https://ffmpeg.org/) - For mp4 to mp3 conversion

<!-- ## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 
 -->
## Authors

* **jayathungek** - *Initial work* - [jayathungek](https://github.com/jayathungek)

<!-- See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project. -->

<!-- ## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details -->

<!-- ## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
 -->