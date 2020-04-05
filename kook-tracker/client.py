from config import Config
import time
import urllib
from bs4 import BeautifulSoup as bs


class Client:
  def __init__(self, app=None):
    self.last_call_time = time.time()
    self.app = app

  @property
  def sleeping(self):
    return time.time() - self.last_call_time < Config.CLIENT_WAIT_SECONDS

  def __call__(self, url):
    while self.sleeping:
      time.sleep(0.01)

    try:
      with urllib.request.urlopen(url) as html:
        if self.app is not None:
          self.app.logger.info('Request to {} successful'.format(url))
        self.last_call_time = time.time()
        return bs(html, 'lxml')

    except urllib.request.HTTPError as e:
      raise Exception('Unrecognized url {}'.format(url)) from e
