from io import BytesIO
import multiprocessing.pool
from pathlib import Path
import pickle
from typing import Generator, Union, List
import requests
import urllib
import urllib.parse
import traceback
from urllib.parse import urlparse
import json
from tqdm import tqdm

import multiprocessing.dummy as mp
import concurrent.futures as cf
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from images.image import Image, ImageFormatter

from bs4 import BeautifulSoup

from utils.threadedgenerator import ThreadedGenerator

class ImagesGatherer():
    def __init__(self) -> None:
        pass

    def gather_images(self):
        return list(self.iterate_images())

    def iterate_images(self, formatter:ImageFormatter=None) -> Generator[Image, str, None]:
        pass

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}>"

class WebApiImgsGatherer(ImagesGatherer):
    def __init__(self, max_count=-1, print_progress=False) -> None:
        super().__init__()
        self.api_url = ""
        self._max_count = max_count if max_count is not None else -1
        self.print_progress = print_progress

    @property
    def max_count(self):
        self._max_count = self.posts_count if self._max_count<0 else min(self.posts_count, self._max_count)
        return self._max_count

    @property
    def posts_count(self):
        return -1

    def make_pbar(self, iterable=None)->tqdm:
        if self.print_progress:
            pbar = tqdm(iterable=iterable, total = self.max_count if self.max_count!=-1 else None)
            return pbar
        else:
            return iterable

    def get_posts(self, page=0) -> List[str]:
        """ returns list of images urls """
        pass

    def sitenable_url(self, url):
        sitenable = "https://sitenable.pw/o.php?b=4&pv=1&mobile=&u="
        url = sitenable + urllib.parse.quote(url)
        return url

    def iterate_posts(self) -> Generator[str, None, None]:
        page = 0
        count = 0
        ended = False

        while not ended:
            posts = self.get_posts(page)
            if posts is None:
                ended = True
            elif len(posts) == 0:
                ended = True
            else:
                for url in posts:
                    if url:
                        yield url
                        count += 1
                        if count >= self.max_count and self.max_count != -1:
                            ended = True
                            return
                page+=1

        yield from []

    def make_request(self, url):
        return requests.get(url)
    
    def request_json(self, url):
        res = self.make_request(url)
        try:
            data = json.loads(res.text)
            return data
        except:
            traceback.print_exc()
        return None
    
    def iterate_images(self, formatter:ImageFormatter=None) -> Generator[Image, str, None]:
        generator = self.iterate_posts()
        print("running workers...")
        pbar = self.make_pbar()

        def process_image(url:str):
            if pbar is not None: pbar.update(1)
            if url.endswith(".gif"): return None
            img = Image.load_from_url(url)
            if formatter is not None:
                img = formatter.format_image(img)
            return img, url

        with ThreadPoolExecutor(max_workers=8) as p:
            futures = {p.submit(process_image, url): url for url in generator}

        if pbar is not None: pbar.close()
        print("getting results...")
        pbar = self.make_pbar(cf.as_completed(futures))
        for future in pbar:
            try:
                img, url = future.result()
                if img is not None:
                    yield img, url
            except:
                pass
        if pbar is not None: pbar.close()

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}>"

class AnimePicsGatherer(WebApiImgsGatherer):
    def __init__(self, max_count=-1, test_cookie="", print_progress=False) -> None:
        super().__init__(max_count, print_progress)
        self.test_cookie = test_cookie

        self.api_url = "http://ashen-hermit.42web.io/anime_pics/api/"
        self.posts_url = self.api_url+"get_posts.php?page={page}"
        self.stats_url = self.api_url+"get_stats.php"

    def request_stats(self):
        print("requesting stats...")
        res = self.make_request(self.stats_url)
        try:
            return json.loads(res.text)
        except:
            traceback.print_exc()
            return {"posts_count":3030, "pages_count":76}

    @property
    def stats(self):
        if getattr(self, "_stats", None) is None:
            self._stats = self.request_stats()
        return self._stats

    @property
    def posts_count(self):
        return self.stats["posts_count"]

    def make_request(self, url):
        return requests.get(url, cookies={"__test": self.test_cookie})

    def request_posts(self, page):
        url = self.posts_url.format(page=page)
        data = self.request_json(url)
        return data

    def get_posts(self, page=0) -> List[str]:
        posts = []
        url = self.posts_url.format(page=page)
        try:
            res = self.make_request(url)
            data:list[dict] = json.loads(res.text)
            for post in data:
                url = post.get("source", "")
                if url:
                    posts.append(url)
        except:
            traceback.print_exc()
        return posts

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} Images Gatherer>"

class Rule34Gatherer(WebApiImgsGatherer):
    def __init__(self, max_count=-1, tags="", print_progress=False) -> None:
        super().__init__(max_count, print_progress)
        self.tags = tags
        
        self.api_url = "https://api.rule34.xxx/"
        self.posts_url = self.api_url+"index.php?page=dapi&s=post&q=index&json=1&pid={page}&limit=1000&tags={tags}"
        self.tag_stats_url = "https://rule34.xxx/index.php?page=tags&s=list&tags={tags}&sort=asc&order_by=index_count"

    def request_posts_count(self):
        if len(self.tags.split(" ")) > 1: return -1
        print("requesting posts count...")
        url = self.tag_stats_url.format(tags=self.tags)
        url = self.sitenable_url(url)
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        el = soup.find("a", string=self.tags) 
        info = el.parent.parent.parent
        count = int(list(info)[0].text)
        return count

    @property
    def posts_count(self):
        if getattr(self, "_posts_count", None) is None:
            self._posts_count = self.request_posts_count()
        return self._posts_count

    def make_request(self, url):
        url = self.sitenable_url(url)
        return requests.get(url)

    def request_posts(self, page):
        url = self.posts_url.format(page=page, tags=self.tags)
        data:list[dict] = self.request_json(url)
        return data

    def get_posts(self, page=0) -> List[str]:
        posts = []
        try:
            data:list[dict] = self.request_posts(page)
            for post in data:
                url = post.get("sample_url", "")
                if url:
                    url = self.sitenable_url(url)
                    posts.append(url)
        except:
            traceback.print_exc()
        return posts

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} with tags=\"{self.tags}\">"

class ListOfUrlsGatherer(WebApiImgsGatherer):
    def __init__(self, urls:List[str]=None, max_count=-1, print_progress=False) -> None:
        super().__init__(max_count, print_progress)
        self.urls = urls or []

    @property
    def posts_count(self):
        return len(self.urls)

    def get_posts(self, page=0) -> List[str]:
        if page==0:
            return self.urls[:self.max_count]
        return []

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}, {len(self.urls)} urls>"