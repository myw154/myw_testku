import os
import re
import sys
import json
import requests
import hashlib
import threading
from time import time
from requests import request
from retrying import retry
from lxml import etree
from threading import Thread
from queue import Queue
from copy import deepcopy


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
from conf import *

class HenanCompy(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_16_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36',
        }
        self.quali_type = QUALI_TYPE
        self.re_page_num = re.compile(r'总共.*?>(\d{2,8})<.*?条')
        self.form_data_list = self._init_form_data()
        self.log_file = open(os.path.join(BASE_DIR,'log/form_data.txt'), 'a+', encoding='utf-8')
        self.err_form_data_file = open(os.path.join(BASE_DIR,'log/err_form_data.txt'), 'a+', encoding='utf-8')
        self.err_form_lock = threading.Lock()
        self.detail_err_file =  open(os.path.join(BASE_DIR,'log/err_detail_url.txt'), 'a+', encoding='utf-8')
        self.detail_file = open(os.path.join(BASE_DIR,'log/detail_url.txt'), 'a+', encoding='utf-8')
        self.log_lock = threading.Lock()
        self.detail_lock = threading.Lock()
        self.q1 = Queue(maxsize=1000)
        self.q2 = Queue(maxsize=1000)
        self.dtail_url_list = self._init_detail_list()
        self.thread_num = 5
        self.alread_num = 0
        self.err_num = 0
        self.err_form_num = 0
        self.err_lock = threading.Lock()


    def _init_form_data(self):
        form_list = set()
        if not os.path.exists(os.path.join(BASE_DIR,'log/form_data.txt')):
            return form_list
        with open(os.path.join(BASE_DIR,'log/form_data.txt'), 'r', encoding='utf-8') as f:
            for i in f:
                form_list.add(i.strip())
        return form_list

    def _init_detail_list(self):
        det_url_list = set()
        if os.path.exists(os.path.join(BASE_DIR,'log/detail_url.txt')):
            with open(os.path.join(BASE_DIR,'log/detail_url.txt'), 'r', encoding='utf-8') as f:
                for i in f:
                    det_url_list.add(i.strip())
        return det_url_list


    @retry(stop_max_attempt_number=6, stop_max_delay=3000, wait_fixed=3000, wait_incrementing_increment=500)
    def send_rquest_get(self, url):
        """
        发送get请求
        """
        requests.packages.urllib3.disable_warnings()
        res = request(method='get', url=url, headers=self.headers, timeout=10)
        try:
            html_str = res.content.decode(encoding='utf-8')
        except Exception as err:
            try:
                html_str = res.content.decode(encoding='GBK')
            except Exception as err:
                try:
                    html_str = res.content.decode(encoding='GB2312')
                except Exception as err:
                    html_str = res.content.decode(encoding='GB18030')
        return html_str

    @retry(stop_max_attempt_number=6, stop_max_delay=3000, wait_fixed=3000, wait_incrementing_increment=500)
    def send_quest_post(self, url, data, headers=None):
        """
        发送post请求
        """
        if not headers:
            headers = self.headers
        requests.packages.urllib3.disable_warnings()
        res = request(method='post', url=url, data=data, headers=headers, timeout=10)
        res_info = res.content.decode(encoding='utf-8')
        return res_info

    def get_page_num(self, html_str):
        if self.re_page_num.search(html_str):
            page_num = int(self.re_page_num.search(html_str).group(1)) // 10 +1
        else:
            page_num = 0
        return page_num

    def get_detail_url(self,html_str, certtypenum):
        html_obj = etree.HTML(html_str)
        tr_obj_list = html_obj.xpath('//div[@id="tagContenth0"]/table/tbody/tr')[1:]
        for tr_obj in tr_obj_list:
            detail_url = 'http://hngcjs.hnjs.gov.cn'+tr_obj.xpath('.//a/@href')[0]
            if detail_url not in self.dtail_url_list:
                #print('详情页的URL：%s' % detail_url)
                self.q2.put((detail_url,certtypenum))

    def get_info(self):
        form_data = {
            '__EVENTTARGET':None,
            '__EVENTARGUMENT': None,
            '__VIEWSTATE': None,
            'page': None,
            'tradetypenum': None,
            'tradeboundnum': None,
            '__VIEWSTATEGENERATOR': 'AB12D588',
            '__EVENTVALIDATION': '/wEdAAnlEV70FrTjlmWb8G2zl/OCcyCwLNtjiGsUsD1klKe8mO/27pz3VRsK7NDdBcWPH1oVz/HNqEavkdJhHEQf0CC9QF5FF4kumzRC1Hm6gbSZLJSStlQIejt9Eiz2dXvmYMkdxEWiDJrToSQwV2qIPrDYCSAehAWh8K/R7+KNdzUNgpSYA6QBBGuDgl6JiXAF2qKw9gjimMdqSvxqmhg71HUxXh4ieFs46FIRmGc4NrfwBw==',
            'certtypenum': None,
            'aptScope': None,
            'aptCode': None,
            'corpname': None,
            'corpcode': None,
            'legalman': None,
            'certid': None,
            'site': None,
            'ry_type': None,
            'ctl09': '搜索'
        }
        for certtypenum in COMPANY_QUALI:
            form_data['certtypenum'] = int(certtypenum)
            form_data['page'] = None
            with self.log_lock:
                self.log_file.write(hashlib.md5(str(form_data).encode(encoding='UTF-8')).hexdigest()+'\n')
                self.log_file.flush()
            html_str = self.send_quest_post(url='http://hngcjs.hnjs.gov.cn/company/list', data=form_data)
            # 解析第一页的情况
            self.get_detail_url(html_str, int(certtypenum))
            page_num = self.get_page_num(html_str)
            for i in range(2, page_num+1):
            #for i in range(2, 4):
                form_data['page'] = i
                if 'ctl09' in form_data:
                    del form_data['ctl09']
                if hashlib.md5(str(form_data).encode(encoding='UTF-8')).hexdigest() in self.form_data_list:
                    continue
                self.q1.put(form_data)

        for i in range(self.thread_num):
            self.q1.put(None)

    def work1(self):
        """
        表单数据请求招标列表页
        """
        print('请求列表页的线程开启.......')
        while True:
            if not self.q1.qsize():
                continue
            form_data = self.q1.get()
            if form_data is None:
                break
            try:
                html_str = self.send_quest_post(url='http://hngcjs.hnjs.gov.cn/company/list', data=form_data)
            except Exception:
                with self.err_form_lock:
                    self.err_form_data_file.write(str(form_data))
                    self.err_form_num += 1
                self.q1.task_done()
                continue
            self.get_detail_url(html_str, form_data['certtypenum'])
            with self.log_lock:
                self.log_file.write(hashlib.md5(str(form_data).encode(encoding='UTF-8')).hexdigest()+'\n')
                self.log_file.flush()
            self.q1.task_done()
        # 每个线程结束的时候放入None
        self.q2.put((None,None))

    def work2(self):
        """
        请求详情页的线程
        """
        print('详情页下载线程开启.......')
        while True:
            if not self.q2.qsize():
                continue
            detail_url, certtypenum = self.q2.get()
            if detail_url is None:
                break
            try:
                res = self.send_rquest_get(detail_url)
            except Exception:
                with self.err_lock:
                    self.detail_err_file.write(detail_url+'\n')
                    self.err_num += 1
                self.q2.task_done()
                continue
            # 文件名字为 网站的ID、certtypenum 的拼接
            file_name = detail_url.split('=')[1]+'__'+str(certtypenum)+'.html'
            file_path = os.path.join(BASE_DIR, 'data', file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(res)

            with self.detail_lock:
                self.detail_file.write(detail_url+'\n')
                self.alread_num += 1
                self.get_already_num()
            self.q2.task_done()

    def get_already_num(self):
        if self.alread_num%1000 == 0:
            print('already download ::: %s' % self.alread_num)

    def run(self):
        thread_list = []
        t1 = Thread(target=self.get_info)
        thread_list.append(t1)
        for i in range(self.thread_num):
            t_work1 = Thread(target=self.work1)
            t_work2 = Thread(target=self.work2)
            thread_list.append(t_work1)
            thread_list.append(t_work2)
        for t in thread_list:
            t.setDaemon(True)
            t.start()
        for t in thread_list:
            t.join()
        print('详情页采集数量：%s \n 详情页出错数量：%s \n 列表页出错数量：%s ' % (self.alread_num, self.err_num, self.err_form_num))

def process():
    henan = HenanCompy()
    henan.run()

if __name__ == '__main__':
    process()



