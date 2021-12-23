#!/bin/bash

function make_setup(){
    setup="import setuptools\nfrom setuptools import find_packages\n\nwith open(\"README.md\", \"r\") as fh:\n    long_description = fh.read()\n\nsetuptools.setup(\n    name=\"ytam\",\n    version=\"$1\",\n    author=\"jayathungek\",\n    author_email=\"jayathunge.work@gmail.com\",\n    description=\"A commandline utility that enables the creation of albums from Youtube playlists.\",\n    long_description=long_description,\n    long_description_content_type=\"text/markdown\",\n    url=\"https://github.com/jayathungek/ytam\",\n    packages=find_packages(),\n    classifiers=[\n        \"Programming Language :: Python :: 3\",\n        \"License :: OSI Approved :: MIT License\",\n        \"Operating System :: OS Independent\",\n    ],\n    python_requires=\">=3.6\",\n    entry_points={\"console_scripts\": [\"ytam=ytam.cmd:main\"],},\n    include_package_data=True,\n    install_requires=[\n        \"certifi\",\n        \"chardet\",\n        \"colorama\",\n        \"idna\",\n        \"mutagen\",\n        \"requests\",\n        \"urllib3\",\n        \"python-ffmpeg\",\n    ],\n)\n"
    printf "$setup"
}

function make_version(){
    version="version = \"$1\""
    printf "$version"
}

make_setup $1 > setup.py
make_version $1 > ytam/version.py

rm -rf dist/ build/ ytam.egg-info/
python setup.py sdist bdist_wheel
twine upload dist/*
