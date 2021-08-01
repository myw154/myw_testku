import os
import re
import sys
import json
import requests
import hashlib
import threading
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
        self.detail_file = open(os.path.join(BASE_DIR,'log/detail_url.txt'), 'a+', encoding='utf-8')
        self.log_lock = threading.Lock()
        self.detail_lock = threading.Lock()
        self.q1 = Queue(maxsize=1000)
        self.q2 = Queue(maxsize=1000)
        self.dtail_url_list = self._init_detail_list()
        self.thread_num = 5


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
        try:
            requests.packages.urllib3.disable_warnings()
            res = request(method='post', url=url, data=data, headers=headers, timeout=10)
            res_info = res.content.decode(encoding='utf-8')
        except Exception as err:
            res_info = ''
        return res_info

    def get_type(self):
        """
        获取资质的筛选项
        """
        certtypenum_url = 'http://hngcjs.hnjs.gov.cn/tBTradetypedic/changeZiZhi'
        tradetype_url = 'http://hngcjs.hnjs.gov.cn/tBTradetypebounddic/changeZiZhi'
        query_data = {"op":"GetTradeTypeNumList", "certtypenum": None}
        query_second = {"op":"GetTradeBoundNumList", "tradetypenum":None}
        new_type_list = []
        for certtypenum, name in self.quali_type.items():
            query_data["certtypenum"] = int(certtypenum)
            res_info = self.send_quest_post(certtypenum_url, query_data)
            res_list = json.loads(res_info)
            for tradetype_dict in res_list:
                query_second['tradetypenum'] = tradetype_dict['tradetypenum']
                second_res = self.send_quest_post(tradetype_url, query_second)
                second_list = json.loads(second_res)
                # for second_dict in second_list:
                    # second_dict['certtypenum'] = int(certtypenum)
                    # second_dict['certtypenum_name'] = name
                tradetype_dict['tradetypenum_next'] = second_list
                new_type_list.append(tradetype_dict)

        with open('type_list.txt', 'w', encoding='utf-8') as f:
            for i in new_type_list:
                f.write(json.dumps(i, ensure_ascii=False)+'\n')

    def last_type(self):
        last_url = "http://hngcjs.hnjs.gov.cn/tBAptitudekinddic/list?certtypenum={}&TradeTypeNum=&tbTradetypebounddic.tradeboundnum={}&tbTradetypedic.tradetypenum={}"
        with open('type_list.txt', 'r', encoding='utf-8') as f:
            for info_dict_str in f:
                info_dict = json.loads(info_dict_str.strip())
                certtypenum = info_dict['certtypenum']
                tradetypenum_dict_list = info_dict['tradetypenum_next']
                for tradetypenum_dict in tradetypenum_dict_list:
                    tradetypenum =tradetypenum_dict["tradetypenum"]
                    tradeboundnum = tradetypenum_dict["tradeboundnum"]
                    url = last_url.format(certtypenum, tradeboundnum, tradetypenum)
                    # form_data = {
                        # 'apt_type':None,
                        # 'complexname':None,
                        # 'apt_root':certtypenum,
                        # 'apt_code2':tradetypenum,
                        # 'apt_code2':tradeboundnum
                    # }
                    # res_html = self.send_quest_post(url)
                    res_html = self.send_rquest_get(url)
                    tradetypenum_dict['last_html'] = res_html
                with open('last_type.txt', 'a+', encoding='utf=8') as f:
                    f.write(json.dumps(info_dict, ensure_ascii=False) + '\n')

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
                print('详情页的URL：%s' % detail_url)
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
        import pdb
        pdb.set_trace()
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
                form_data['page'] = i
                if 'ctl09' in form_data:
                    del format['ctl09']
                if hashlib.md5(str(form_data).encode(encoding='UTF-8')).hexdigest() in self.form_data_list:
                    continue
                self.q1.put(form_data)

        for i in range(self.thread_num):
            self.q1.put(None)

    def work1(self):
        """
        表单数据请求招标列表页
        """
        while True:
            if not self.q1.qsize():
                continue
            form_data = self.q1.get()
            if form_data is None:
                break
            html_str = self.send_quest_post(url='http://hngcjs.hnjs.gov.cn/company/list', data=form_data)
            self.get_detail_url(html_str, form_data['certtypenum'])
            with self.log_lock:
                self.log_file.write(hashlib.md5(str(form_data).encode(encoding='UTF-8')).hexdigest()+'\n')
                self.log_file.flush()
            self.q1.task_done()
        # 每个线程结束的时候放入None
        self.q2.put((None,None))

    def work2(self):
        while True:
            if not self.q2.qsize():
                continue
            detail_ur, certtypenum = self.q2.get()
            if detail_url is None:
                break
            res = self.send_rquest_get(detail_url)
            # 文件名字为 时间戳、网站的ID、certtypenum 的拼接
            file_name = detail_ur.split('=')[1]+'__'+str(certtypenum)+'.html'
            file_path = os.path.join(BASE_DIR, 'data', file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(res)

            with self.detail_lock:
                self.detail_file.write(detail_ur+'\n')
            self.q2.task_done()


    def run(self):
        #self.get_type()
        #self.last_type()
        self.get_info()


def process():
    henan = HenanCompy()
    henan.run()

if __name__ == '__main__':
    process()



