from io import BytesIO
from os import stat
from pathlib import Path
from typing import List, Union
import requests
import urllib
import traceback
import pickle
import gzip

from images.image import Image, ImageFormatter
from images.gatherer import ImagesGatherer, AnimePicsGatherer, Rule34Gatherer
from storable import StorableDriver
from utils.threadedgenerator import ThreadedGenerator

CWD = Path(__file__).parent.resolve() if "__file__" in globals() else Path("C:/Users/user/Python/anime_estimator/images")

class ImagesLibrary(StorableDriver):
    def __init__(self, filepath:Path=None) -> None:
        super().__init__("images", filepath)
        self.images:list[Image] = []

    def __str__(self) -> str:
        im_count = len(self.images)
        s = "" if im_count==1 else "s"
        return f"<{self.__class__.__name__} \"{self.filepath.name}\" ({im_count} image{s})>"

    def load(self):
        print(f"loading {self}...")
        return super().load()

    def save(self):
        print(f"saving {self}...")
        return super().save()

    def add_with_gatherer(self, gatherer:Union[ImagesGatherer, List[ImagesGatherer]], formatter:ImageFormatter=None):
        def iterate_gatherer(gth:ImagesGatherer):
            print(f"gathering images with {gth}...")
            for img, url in gth.iterate_images(formatter=formatter):
                if img is not None:
                    self.images.append(img)

        if type(gatherer) == list:
            for gth in gatherer:
                iterate_gatherer(gth)
        else: 
            iterate_gatherer(gatherer)

    def apply_formatter(self, formatter:ImageFormatter):
        for i, img in enumerate(self.images):
            if img is not None:
                img = formatter.format_image(img)
                self.images[i] = img


def save_anime_pics():
    library = ImagesLibrary(CWD / "anime_pics.dat.gz")
    formatter = ImageFormatter(width=256, height=256)
    print("gathering...")
    gatherer = AnimePicsGatherer(max_count=-1, test_cookie="8ae029db345ca3b89ca44d9d0bed3bdb", print_progress=True)
    library.add_with_gatherer(gatherer, formatter)
    print("saving...")
    library.save()

def save_rule34_bad_drawings():
    library = ImagesLibrary(CWD / "bad_rule34.dat.gz")
    formatter = ImageFormatter(width=256, height=256)

    artists = ["furball", "zeglo-official", "sawacoe", "ftnranat"]
    for artist in artists:
        print(f"gathering \"{artist}\"...")
        gatherer = Rule34Gatherer(max_count=-1, tags=artist, print_progress=True)
        library.add_with_gatherer(gatherer, formatter)
    print("saving...")
    library.save()

def main():
    # save_rule34_bad_drawings()
    pass

if __name__ == '__main__': 
    main()