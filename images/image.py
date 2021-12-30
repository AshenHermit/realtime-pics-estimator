import numpy as np
from io import BytesIO
from os import stat
from pathlib import Path
import pickle
import PIL.Image
from typing import Union
import requests
import urllib
import traceback

class Image():
    def __init__(self, img:PIL.Image.Image):
        self._img:PIL.Image.Image = img

    def convert(self, mode=None, matrix=None, dither=None, palette=PIL.Image.WEB, colors=256):
        return Image(self._img.convert(mode, matrix, dither, palette, colors))

    def __getattr__(self, key):
        if key == '_img':
            #  http://nedbatchelder.com/blog/201010/surprising_getattr_recursion.html
            raise AttributeError()
        return getattr(self._img, key)
    
    @staticmethod
    def open(fp:Union[str, bytes, Path], mode="r"):
        return Image(PIL.Image.open(fp, mode))
    
    @staticmethod
    def load_from_url(url:str, **kwargs):
        """`kwargs` - args for requests.get method """
        try:
            res = requests.get(url, **kwargs)
            return Image.open(BytesIO(res.content))
        except:
            traceback.print_exc()
        
        return None

    @staticmethod
    def from_numpy(n:np.array):
        return 

class ImageFormatter:
    def __init__(self, width=None, height=None, grayscale=False) -> None:
        self.width = width
        self.height = height
        self.grayscale = grayscale

    def format_image(self, img:Image):
        img = img._img
        if self.width or self.height:
            w = self.width or img.width
            h = self.height or img.height
            img = img.resize((w, h))
        if self.grayscale:
            img = img.convert('L')

        return img
