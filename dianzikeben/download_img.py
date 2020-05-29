import sys
import os
import json
from requests import request
from retrying import retry

class DownLoad(object):

    def __init__(self, file_path, img_path):
        self.file_path = file_path
        self.img_path = img_path
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36',
        }

    @retry(stop_max_attempt_number=5, stop_max_delay=3000, wait_fixed=3000, wait_incrementing_increment=500)
    def download_img(self, img_url):
        print(img_url)
        res = request(method='get', url=img_url,headers=self.headers)
        return res

    def store_img(self, img_data, img_url):
        #img_name = '_'.join(img_url.split('/')[3:]).split('.')[0]
        img_name = img_url.replace('/', '~~~').replace(':', '___')
        img_store_path = os.path.join(self.img_path, img_name+'.png')
        with open(img_store_path, 'wb') as f:
            f.write(img_data)

    def book_img_list(self, img_url_list):
        for img_url in img_url_list:
            if img_url.startswith('http'):
                try:
                    print(img_url)
                    res = self.download_img(img_url.strip())
                    if res.status_code == 200:
                    # 存储图片
                        self.store_img(res.content, img_url.strip())
                except Exception:
                    with open(os.path.dirname(self.file_path)+'/img_url_error.txt', 'a', encoding='utf-8') as f:
                        f.write(img_url+'\n')

    def error_img_url(self):
        with open(os.path.dirname(self.file_path)+'/img_url_error.txt', 'r', encoding='utf-8') as f:
            img_url_list = f.readlines()
            print(len(img_url_list))
            for img_url in img_url_list:
                try:
                    #print(img_url.replace('\n', ''))
                    res = self.download_img(img_url.strip())
                    print(res.status_code)
                    if res.status_code == 200:
                    # 存储图片
                        self.store_img(res.content, img_url.strip())
                    else:
                        with open(os.path.dirname(self.file_path)+'/img_url_404.txt', 'a', encoding='utf-8') as f:
                            f.write(img_url)
                except Exception:
                    with open(os.path.dirname(self.file_path)+'/img_url_error2.txt', 'a', encoding='utf-8') as f:
                        f.write(img_url)



def remind():
    if len(sys.argv) < 3:
        print('参数错误')
        sys.exit(-1)


def process():
    remind()
    # 待下载文件的路径
    file_path = sys.argv[1]
    # 图片保存的路径
    img_path = sys.argv[2]
    dowload_img = DownLoad(file_path, img_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        info_dict_str_list = f.readlines()
    for info_dict_str in info_dict_str_list:
        info_dict = json.loads(info_dict_str)
        img_url_list = info_dict['pages']
        dowload_img.book_img_list(img_url_list)


def main():
    remind()
    # 待下载文件的路径
    file_path = sys.argv[1]
    # 图片保存的路径
    img_path = sys.argv[2]
    dowload_img = DownLoad(file_path, img_path)
    dowload_img.error_img_url()

if __name__ == '__main__':
    main()
