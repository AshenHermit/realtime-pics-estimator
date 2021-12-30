from io import BytesIO
from os import stat
from pathlib import Path
from typing import Union
import requests
import urllib
import traceback
import pickle
import gzip

from images.image import Image, ImageFormatter
from images.gatherer import ImagesGatherer, AnimePicsGatherer, Rule34Gatherer

CWD = Path(__file__).parent.resolve()

class StorableDriver:
    def __init__(self, storable_attr="storable_data", filepath:Path=None) -> None:
        self.storable_attr = storable_attr
        self.filepath = filepath or CWD/(self.storable_attr+".dat")
    
    def save(self):
        data = getattr(self, self.storable_attr, None)
        if data is not None:
            try:
                with gzip.GzipFile(str(self.filepath), "wb") as file:
                    pickle.dump(data, file)
            except:
                traceback.print_exc()

    def load(self):
        try:
            with gzip.GzipFile(str(self.filepath), "rb") as file:
                data = pickle.load(file)
            setattr(self, self.storable_attr, data)
        except:
            traceback.print_exc()
        return self