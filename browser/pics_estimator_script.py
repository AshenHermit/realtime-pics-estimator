from threading import Thread
from typing import List
import urllib
import urllib.parse
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import inspect
import json
import time
from anime_estimator import AnimePicEstimator
from images import image
from images.gatherer import ListOfUrlsGatherer
from images.image import Image
from browser.script import Script, script_reg, js_accessable

import concurrent.futures as cf
from concurrent.futures import ThreadPoolExecutor

import asyncio

CWD = Path(__file__).parent.resolve()

@script_reg
class PicsEstimatorScript(Script):
    def __init__(self) -> None:
        super().__init__(
            id="pics_estimator_script",
            javascript_file=CWD/"js/picsEstimator.js",
            script_class_name="PicsEstimatorScript")

        self.estimator = AnimePicEstimator()
        self.estimator.estimator.model
        self.estimation_thread = None

    @js_accessable
    def estimate_image(self, url:str):
        return self.estimate_image_from_url(url)

    @property
    def cookies(self):
        if getattr(self, "_cookies", None) is None or True: # - attension
            if self._driver:
                cookies_list = self._driver.get_cookies()
                self._cookies = {cookie['name']:cookie['value'] for cookie in cookies_list}
            else: 
                self._cookies = {}
        return self._cookies

    @property
    def headers(self):
        if getattr(self, "_headers", None) is None or True: # - attension
            if self._driver:
                parsed_uri = urllib.parse.urlparse(self._driver.current_url)
                referer = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                headers = {
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                    'Referer': referer,
                    'sec-ch-ua-mobile': '?0',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                    'sec-ch-ua-platform': '"Windows"',
                }
                self._headers = headers
            else: 
                self._headers = {}
        return self._headers

    def estimate_image(self, img):
        value = self.estimator.estimate(img)
        value = float(value.numpy()[0][0])
        return value

    def estimate_image_from_url(self, url:str):
        img = Image.load_from_url(url, cookies=self.cookies, headers=self.headers)
        if img is not None:
            return self.estimate_image(img._img)
        return None

    def run_estimation_thread(self, urls:List[str]):
        def estimate(url):
            estimation = self.estimate_image_from_url(url)
            self.js.onImageEstimated(url, estimation)

        with ThreadPoolExecutor(max_workers=10) as p:
            futures = {p.submit(estimate, url): url for url in urls}
        
        # for future in futures:
        #     future.result()

    @js_accessable
    def estimate_images_with_callback(self, urls:List[str]):
        # gatherer = ListOfUrlsGatherer(urls=urls, print_progress=True)
        # for img, url in gatherer.iterate_images():
        #     estimation = self.estimate_image(img)
        #     self.js.onImageEstimated(url, estimation)
        
        if self.estimation_thread is not None: self.estimation_thread.join()
        self.estimation_thread = Thread(target=self.run_estimation_thread, args=(urls,))
        self.estimation_thread.start()

        