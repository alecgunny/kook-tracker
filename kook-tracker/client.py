import time
import urllib
from functools import lru_cache

from bs4 import BeautifulSoup as bs
from config import Config


class Client:
    def __init__(self, app=None):
        self.app = app

    def get_ttl_hash(self):
        """Return the same value withing `seconds` time period"""
        return round(time.time() / Config.CLIENT_WAIT_SECONDS)

    @lru_cache
    def make_request(self, url, ttl_hash=None):
        try:
            with urllib.request.urlopen(url) as html:
                if self.app is not None:
                    self.app.logger.info(f"Request to {url} successful")
                return bs(html, "lxml")

        except urllib.request.HTTPError as e:
            raise Exception("Unrecognized url {}".format(url)) from e

    @lru_cache
    def __call__(self, url):
        self.make_request(url, ttl_hash=self.get_ttl_hash())
