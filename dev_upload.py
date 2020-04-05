import base64
import json
import logging
import math
import mimetypes
import os
import time

import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

login_url = "https://cowtransfer.com/user/emaillogin"
info_url = "https://cowtransfer.com/space/in/info"
prepare_send_url = "https://cowtransfer.com/transfer/preparesend"
before_upload_url = "https://cowtransfer.com/transfer/beforeupload"
uploaded_url = "https://cowtransfer.com/transfer/uploaded"
complete_url = "https://cowtransfer.com/transfer/complete"

qiniu_upload_url = "https://upload.qiniup.com/"
qiniu_upload_mkblk = "https://upload.qiniup.com/mkblk/"
qiniu_upload_mkfile = "https://upload.qiniup.com/mkfile/%s/key/%s/fname/%s"

headers = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_4 like Mac OS X) '
                         'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}


d = {}
fileId = ''


def cow_upload(fileName):
    fname = fileName
    session = requests.Session()

    def fileSize(file):
        size = os.path.getsize(file)
        return size

    def paramsPrepareSend(s):
        dic = json.loads(s)
        return dic

    def fileMimeTypes(file):
        ret = mimetypes.guess_type(file)[0]
        return ret

    def before_upload():
        global d, fileId
        prepare_send_data = {
            "totalSize": fileSize(fname),
            "language": "zh-cn",
            "validDays": 7,
            "saveToMyCloud": "false",
            "downloadTimes": -1,
            "enableShareToOthers": "false"
        }

        # r_login = session.post(login_url, headers=headers, params=login_data, timeout=20)
        r_prepare_send = session.post(prepare_send_url, params=prepare_send_data, headers=headers, timeout=20)
        logging.debug(r_prepare_send.text)
        d = paramsPrepareSend(r_prepare_send.text)

        fileId = "%s-%s" % (fname, int(time.time() * 1000))
        before_upload_data = {
            "type": fileMimeTypes(fname),
            "fileId": fileId,
            "fileName": fname,
            "fileSize": fileSize(fname),
            "transferGuid": d['transferguid'],
            "storagePrefix": d['prefix'],
        }
        r_before_upload = session.post(before_upload_url, params=before_upload_data, headers=headers, timeout=20)
        logging.debug(r_before_upload.text)

    def upload():
        upload_progress = 0,0
        uploaded_data = []

        def my_callback(monitor):
            progress = (monitor.bytes_read / monitor.len) * 100
            print("\r上传进度：%d%%(%d/%d),总进度:%d/%d"
                  % (progress, monitor.bytes_read, monitor.len, upload_progress[0]+1, upload_progress[1]), end=" ")

        def upload_stream(upload_url, stream):
            e = MultipartEncoder({"file": stream})
            m = MultipartEncoderMonitor(e, my_callback)
            r = requests.post(upload_url, data=m,
                              headers={'Authorization': "UpToken %s" % d['uptoken'],
                                       'Content-Type': m.content_type})
            logging.debug(len(stream))
            return r.text

        def split_file():
            nonlocal upload_progress
            start_time = time.time()
            f_pice = math.ceil(fileSize(fname) / (4194304 - 123))
            f = open(fname, "rb")
            while True:
                temp = f.read(4194304 - 123)
                if len(temp) != 0:
                    length = len(temp) + 123
                    upload_mkblk = qiniu_upload_mkblk + str(length)
                    upload_progress = (len(uploaded_data), f_pice)
                    ret = upload_stream(upload_mkblk, temp)
                    upload_progress = (len(uploaded_data)+1, f_pice)
                    uploaded_data.append(json.loads(ret))
                    logging.debug(upload_mkblk)
                else:
                    break
            end_time = time.time()
            print("\n文件：%s,上传完成,用时：%.1fs" % (fname, end_time - start_time))
            return uploaded_data

        def mkfile():
            authorization = {'Authorization': "UpToken %s" % d['uptoken'],
                             'Content-Type': 'text/plain'}
            headers_authorization = dict(headers, **authorization)
            filename = base64.urlsafe_b64encode(fname.encode())
            filepath = base64.urlsafe_b64encode(("%s/%s/%s" % (d['prefix'], d['transferguid'], fname)).encode())

            s = []
            offset = 0
            for item in uploaded_data:
                s.append(item['ctx'])
                offset += item['offset']

            upload_mkfile = qiniu_upload_mkfile % (offset, filepath.decode(), filename.decode())
            ctx = ",".join(s)
            logging.debug(ctx)

            r_qiniu_mkfile = requests.post(upload_mkfile, headers=headers_authorization, data=ctx)
            logging.debug(r_qiniu_mkfile.text)

        split_file()
        mkfile()

    def after_upload():
        uploaded = {
            "fileId": fileId,
            "transferGuid": d['transferguid'],
        }
        r_uploaded = session.post(uploaded_url, params=uploaded, headers=headers, timeout=20)
        logging.debug(r_uploaded.text)
        complete_data = {
            "transferGuid": d['transferguid'],
        }
        r_complete = session.post(complete_url, params=complete_data, headers=headers, timeout=20)
        r = paramsPrepareSend(r_complete.text)
        logging.debug(r_complete.text)
        print("文件永久链接：%s 取件码：%s" % (d['uniqueurl'], r['tempDownloadCode']))

    before_upload()
    upload()
    after_upload()
