from __future__ import absolute_import

import logging
import requests
import json
import os
import sys
import errno
import shutil

from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class API:
    def __init__(self, site_url, dump = False):
        self.log = logging.getLogger(__name__)
        self.site_url = site_url
        self.api_url = site_url + 'static/json/'
        self.image_url = site_url + 'img/c/'
        self.dump = dump

    def get_json(self, *args):
        path = '/'.join(args)
        self.log.debug('request to %s%s', self.api_url, path)
        with requests.Session() as s:
            retries = Retry(
                total=10,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504])
            s.mount('http://', HTTPAdapter(max_retries=retries))
            s.mount('https://', HTTPAdapter(max_retries=retries))
            response = s.get(self.api_url + path, verify=False)
        self.log.debug('result %s', response.json())
        if self.dump:
            self.log.debug('dumping json %s', path)
            filename = datetime.now().strftime('json/%Y%m%d/') + path
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            with open(filename, 'w') as outfile:
                json.dump(response.json(), outfile)
        return response.json()

    def get_image(self, filename, *args):
        path = '/'.join(args)
        self.log.debug('download from %s%s', self.image_url, path)
        try:
            response = requests.get(self.image_url + path, stream=True, verify=False)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
        except:
            e = sys.exc_info()[0]
            self.log.error(e)
