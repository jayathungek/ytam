import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ytam-jayathungek", #change to ytam
    version="0.0.1",
    author="jayathungek",
    author_email="jayathunge.work@gmail.com",
    description="A commandline utility that enables the creation of albums from Youtube playlists.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)