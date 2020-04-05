import json
import logging
import os
import time
from contextlib import closing

import requests

# logging.basicConfig(level=logging.WARNING)
s_url = 'https://cowtransfer.com/s/'
transferdetail_url = 'https://cowtransfer.com/transfer/transferdetail'
zippingstatus_url = 'https://cowtransfer.com/transfer/zippingstatus'
download_url = 'https://cowtransfer.com/transfer/download'

headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Mobile Safari/537.36',
           'Connection': 'keep-alive'}


def get_url_download(cow_prefix):
    transferdetail_data = {
        'url': cow_prefix,
    }

    session = requests.Session()
    r_transferdetail = session.get(transferdetail_url, headers=headers, params=transferdetail_data, timeout=20)
    d = json.loads(r_transferdetail.text)
    logging.info(r_transferdetail.text)

    download_data = {
        'guid': d['transferFileDtos'][0]['guid']
    }
    zippingstatus_data = {
        'guid': d['guid']
    }

    r_zippingstatus = session.get(zippingstatus_url, headers=headers, params=zippingstatus_data, timeout=20)
    logging.info(r_zippingstatus.text)
    referer = {'Referer': "%s%s" % (s_url, cow_prefix)}
    headers_referer = dict(headers, **referer)
    r_download = session.post(download_url, headers=headers_referer, params=download_data, timeout=20)
    d = json.loads(r_download.text)
    logging.info(r_download.text)
    logging.info(d['link'])
    return d['link']


def log_download(fileUrl, fileName):
    with closing(requests.get(fileUrl, headers=headers, stream=True)) as response:
        chunkSize = 1024
        contentSize = int(response.headers['content-length'])
        dateCount = 0
        filePath = os.path.join(os.getcwd(), fileName)
        with open(filePath, "wb") as file:
            for data in response.iter_content(chunk_size=chunkSize):
                file.write(data)
                dateCount = dateCount + len(data)
                nowJd = (dateCount / contentSize) * 100
                print("\r 文件下载进度: %d%%(%d/%d) - %s" % (nowJd, dateCount / 1024, contentSize / 1024, fileName), end='')


def cow_download(prefix):
    start_time = time.time()
    verifyDownloadCode_url = 'https://cowtransfer.com/transfer/verifydownloadcode?code=%s'

    def download_code(code):
        Code_url = verifyDownloadCode_url % code
        r_Code = requests.get(Code_url, headers=headers, timeout=20)
        return json.loads(r_Code.text)['url']

    if len(prefix) == 6:
        prefix = download_code(prefix)
    ret = get_url_download(prefix)
    if len(ret) != 0:
        fileName = ret.split("//")[1].split('?')[0].split('/')[-1]
        log_download(ret, fileName)
    end_time = time.time()
    print("\n下载完成,用时:%.2fs" % (end_time-start_time))
