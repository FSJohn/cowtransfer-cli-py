# -*- coding:utf-8 -*-
# author: FSJohn
# Date: 2020.04.04
# v0.0.1

import getopt
import logging
import sys

import dev_upload
import dev_download
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


def main():
    opts, args = getopt.getopt(sys.argv[1:], '-h-u:-d:-v:', ['help', 'up=', 'down=', 'version'])
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            print("-u [filename/filepath]")
            print("-d [url]")
            exit()
        if opt_name in ('-v', '--version'):
            print("Version is 0.01 ")
            exit()
        if opt_name in ('-u', '--up'):
            fileName = opt_value
            print("Upload:", fileName)
            dev_upload.cow_upload(fileName)
        if opt_name in ('-d', '--down'):
            url = opt_value
            print("Download:", url)
            dev_download.cow_download(url)
            exit()


if __name__ == "__main__":
    main()
