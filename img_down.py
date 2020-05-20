import requests
import re
import os
import schedule
import pdb
import time
from datetime import datetime
from retrying import retry
from requests import request
from setting import SUBJECT_ID, START_URL, HEADERS, IMG_HEADERS
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ImgDown(object):
    def __init__(self):
        self.img_headers = IMG_HEADERS
        self.img_err_f = open(os.path.join(BASE_DIR, 'log/del_img_err'), 'a')  # 图片下载错误的文件

    @retry(stop_max_attempt_number=7, stop_max_delay=6000, wait_fixed=3000, wait_incrementing_increment=500)
    def _send_request(self, url, headers=None):
        requests.packages.urllib3.disable_warnings()
        res = request(method='get', url=url, headers=headers, timeout=10, verify=False)
        return res

    # 图片下载
    def _down_img(self, img_url):
        try:
            res = self._send_request(img_url, headers=self.img_headers)
        except Exception as err:
            self.img_err_f.write(img_url+'\n')
            self.img_err_f.flush()
            return
        img_name = img_url.replace('/', '~~~')
        img_path = os.path.join(BASE_DIR, 'data/img',img_name+'.png')
        with open(img_path, 'wb') as f:
            f.write(res.content)
        im = Image.open(img_path)
        im.save(img_path)

    def _err_img_down(self):
        print('开始下载错误图片的地址')
        f =  open(os.path.join(BASE_DIR, 'log/img_err'), 'r')
        i = 0
        for url_str in f:
            if not url_str:
                continue
            self._down_img(url_str.strip())
            i += 1
        print('错误图片地址已经下载完了:::数量为：%s' % i)

def img_stask():
    img_down = ImgDown()
    img_down._err_img_down()

def main():
    schedule.every().day.at("23:55").do(img_stask)
    while True:
        # 启动服务
        schedule.run_pending()
        time.sleep(5)

if __name__ == '__main__':
    main()


