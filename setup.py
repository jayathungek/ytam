import setuptools
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ytam",
    version="0.0.33",
    author="jayathungek",
    author_email="jayathunge.work@gmail.com",
    description="A commandline utility that enables the creation of albums from Youtube playlists.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jayathungek/ytam",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points = {
        'console_scripts': ['ytam=ytam.cmd:main'],
    },
    include_package_data=True,
    install_requires=[
        "certifi",
        "chardet",
        "colorama",
        "idna",
        "mutagen",
        "requests",
        "urllib3",
        "python-ffmpeg"
    ]
)