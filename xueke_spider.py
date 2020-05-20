import requests
import re
import os
import json
import pdb
import hashlib
import time
from datetime import datetime
from copy import deepcopy
from retrying import retry
from lxml import etree
from bs4 import BeautifulSoup
from requests import request
from setting import SUBJECT_ID, START_URL, HEADERS, IMG_HEADERS
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class XueKe(object):
    def __init__(self):
        self._gen_dir_path()
        self.start_url_list = START_URL.items()
        self.headers = HEADERS
        self.img_headers = IMG_HEADERS
        self.end_date = datetime.strptime('2019-01-01', '%Y-%m-%d')
        self.parse_img_url = 'http://im.zujuan.xkw.com/Parse/{}/{}/843/14/28/{}'
        self.anwer_img_url = 'http://im.zujuan.xkw.com/Answer/{}/{}/843/14/28/{}'
        self.page_err_f = open(os.path.join(BASE_DIR, 'log/page_err'), 'a') # 一页错误的文件
        self.know_err_f = open(os.path.join(BASE_DIR, 'log/know_page_err'), 'a') # 一个知识点错误的文件
        self.subject_err_f = open(os.path.join(BASE_DIR, 'log/subject_err'), 'a') # 一个科目错误的文件
        self.form_file = open(os.path.join(BASE_DIR, 'log/form_data_fille'), 'a')
        self.form_data_set = set()
        self._init_form_data()
    '''
    def __del__ (self):
        os.renames(os.path.join(BASE_DIR, 'log/img_err'),os.path.join(BASE_DIR, 'log/img_err_1'))
    '''

    def _init_form_data(self):
        log_form_path = os.path.join(BASE_DIR, 'log/form_data_fille')
        if not os.path.exists(log_form_path):
            return
        f = open(log_form_path, 'r', encoding='utf-8')
        for info in f:
            self.form_data_set.add(info.strip())
        f.close()

    # 生成必要的文件路径
    def _gen_dir_path(self):
        dir_path = os.path.join(BASE_DIR, 'log')
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        img_path = os.path.join(BASE_DIR, 'data/img')
        if not os.path.exists(img_path):
            os.makedirs(img_path)

    @retry(stop_max_attempt_number=7, stop_max_delay=6000, wait_fixed=3000, wait_incrementing_increment=500)
    def _send_request(self, url, headers=None):
        requests.packages.urllib3.disable_warnings()
        res = request(method='get', url=url, headers=headers, timeout=10, verify=False)
        return res

    # 转换成html字符串
    def _bytes_to_str(self, res):
        try:
            html_str = res.content.decode(encoding='utf-8')
        except Exception:
            try:
                html_str = res.content.decode(encoding='gbk')
            except Exception:
                try:
                    html_str = res.content.decode(encoding='GB2312')
                except Exception:
                    html_str = res.content.decode(encoding='GB18030')
        return html_str

    # 获取目录html
    def _get_treeitem(self, url):
        res = self._send_request(url, headers=self.headers)
        html_str = self._bytes_to_str(res)
        html_obj = etree.HTML(html_str)
        li_obj_list = html_obj.xpath('.//div[@class="tk-tree tree-root"]/ul/li')
        self.url_list = []
        self._parse_treeitme(li_obj_list)

    # 获得目录的最里层的url
    def _parse_treeitme(self, li_obj_list):
        for li_obj in li_obj_list:
            title = li_obj.xpath('./div/a/text()')[0]
            a_url = li_obj.xpath('./div/a/@href')[0]
            ul = li_obj.xpath('./ul')
            if ul:
                new_li_obj = ul[0].xpath('./li')
                self._parse_treeitme(new_li_obj)
            else:
                self.url_list.append({title:a_url})

    # 生成文件句柄
    def _get_file_hand(self, period, subject, file_name):
        dir_path = os.path.join(BASE_DIR, 'data', period, subject)
        file_path = os.path.join(dir_path,  file_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        f = open(file_path, 'a', encoding='utf-8')
        return f

    def _get_all_ques(self, period_sub, title, url):
        res = self._send_request(url, self.headers)
        html_str = self._bytes_to_str(res)
        p_num = self._get_ques_pages(html_str)
        if not p_num:
            return
        page_url = url+'qs-1o2p{}/'
        f_write = self._get_file_hand(period_sub[:2], period_sub[2:], title)
        for num in range(1, p_num+1):
            url = page_url.format(num)
            try:
                self._date_circle()
                self._get_per_page(period_sub, url, f_write)
                print('%s:::%s:::第 %s 页:::已采集' % (period_sub, title, num))
            except Exception as err:
                self.page_err_f.write('%s:::%s:::%s\n' % (period_sub, title, url))
                self.page_err_f.flush()

    # 时间循环判断
    def _date_circle(self):
        cur_minute = datetime.now().minute
        cur_hour = datetime.now().hour
        new_time = datetime.strptime('{}{}'.format(cur_hour, cur_minute),'%H%M')
        start_time = datetime.strptime('02','%H%M')
        end_time = datetime.strptime('2355','%H%M')
        while not start_time <= new_time <= end_time:
            time.sleep(5)
            print('循环等待中.....')
            cur_minute = datetime.now().minute
            cur_hour = datetime.now().hour
            new_time = datetime.strptime('{}{}'.format(cur_hour, cur_minute),'%H%M')

    # 获得每一页的试题
    def _get_per_page(self, period_sub, url, f_wr):
        hex_url = hashlib.md5(url.encode(encoding='UTF-8')).hexdigest()
        if hex_url in self.form_data_set:
            return
        res = self._send_request(url, self.headers)
        html_str = self._bytes_to_str(res)
        html_obj = etree.HTML(html_str)
        div_list = html_obj.xpath('.//section[@class="test-list"]/div')
        if len(div_list)==0:
            return
        self._store_qus(period_sub, url, f_wr, div_list, hex_url)

    # 存储试题
    def _store_qus(self, period_sub, url, f_wr, div_list, hex_url):
        for div_obj in div_list:
            ques_dict = {}
            str_data = div_obj.xpath('.//div[@class="info left fl"]/span[1]/text()')[0] # 试题日期
            ques_data = datetime.strptime(str_data.split('：')[-1], '%Y/%m/%d')
            if ques_data < self.end_date:
                ques_dict['flag'] = True
            else:
                ques_dict['flag'] = False
            period = period_sub[:2] # 学段
            ques_dict['period'] = period
            subject = period_sub[2:] # 学科
            ques_dict['subject'] = subject
            sub_id = SUBJECT_ID[period_sub]
            ques_id = div_obj.xpath('./div[@class="quesdiv question-inner"]/@id')[0].replace('quesdiv', '') # 试题id
            ques_dict['source'] = ques_id
            img_key = div_obj.xpath('./div[@class="quesdiv question-inner"]/@key')[0]
            diff_str = div_obj.xpath('.//div[@class="info left fl"]/span[2]/text()')[0] # 试题难度
            ques_dict['orig_diff'] = float(diff_str.split('：')[-1])
            ques_dict['difficulty'] = float(diff_str.split('：')[-1])
            type_str = div_obj.xpath('.//div[@class="info left fl"]/span[3]/text()')[0] # 试题类型
            ques_dict['type'] = type_str.split('：')[-1]
            parser_img = self.parse_img_url.format(ques_id, sub_id, img_key) # 解析图片url
            answer_img = self.anwer_img_url.format(ques_id, sub_id, img_key) # 答案图片地址
            ques_dict['parser_img'] = parser_img
            ques_dict['answer_img'] = answer_img
            ques_dict['stem_str'] = etree.tostring(div_obj, encoding='utf-8').decode()
            f_wr.write(json.dumps(ques_dict, ensure_ascii=False)+'\n')
            f_wr.flush()
            self._down_img(parser_img)
            self._down_img(answer_img)
        self.form_file.write(hex_url+'\n')
        self.form_file.flush()

    # 图片下载
    def _down_img(self, img_url):
        try:
            res = self._send_request(img_url, headers=self.img_headers)
        except Exception as err:
            with open(os.path.join(BASE_DIR, 'log/img_err'), 'a') as f:
                f.write(img_url+'\n')
            return
        img_name = img_url.replace('/', '~~~')
        img_path = os.path.join(BASE_DIR, 'data/img',img_name+'.png')
        with open(img_path, 'wb') as f:
            f.write(res.content)
        im = Image.open(img_path)
        im.save(img_path)

    def _err_img_down(self):
        f =  open(os.path.join(BASE_DIR, 'log/img_err_1'), 'r')
        for url_str in f:
            if not url_str:
                continue
            self._down_img(url_str.strip())

    def _err_page_ques(self, period_sub, title, url):
        f_write = self._get_file_hand(period_sub[:2], period_sub[2:], title)
        try:
            flag = self._get_per_page(period_sub, url, f_write)
            print('%s:::%s:::第 %s 页:::已采集' % (period_sub, title, url))
        except Exception as err:
            self.page_err_f.write('%s:::%s:::%s\n' % (period_sub, title, url))
            self.page_err_f.flush()

    def _err_all_page(self):
        f = open(os.path.join(BASE_DIR, 'log/page_err_1'), 'r')
        for info_line in f:
            info_list = info_line.strip().split(':::')
            self._err_page_ques(*info_list)


    # 获得总页数
    def _get_ques_pages(self, html_str):
        html_obj = etree.HTML(html_str)
        page_num_list = html_obj.xpath('.//a[@id="lastpage"]/@lastid')
        if page_num_list:
            page_num = html_obj.xpath('.//a[@id="lastpage"]/@lastid')[0] 
            p_num = int(page_num)
        else:
            p_num = False
        return p_num

    '''
    def test_tree(self):
        for start_url in list(START_URL.values())[:1]:
            self._get_treeitem(start_url)

    '''
    '''
    # 所有科目
    ['小学语文', '小学数学', '小学英语', '小学科学', '小学道德与法治', '初中语文', '初中数学',
    '初中英语', '初中物理', '初 中化学', '初中生物', '初中地理', '初中道德与法治', '初中历史',
    '初中历史与社会', '初中科学', '初中信息技术', '高中语文', '高中数学', '高中英语', '高中物理',
    '高中化学', '高中生物', '高中政治', '高中历史', '高中地理', '高中信息技术', '高中通用技术']
    '''
    def run(self):
        subject_list = ['高中语文', '高中英语', '高中物理', '高中化学', '高中生物', '高中政治']
        for period_sub, start_url in self.start_url_list:
            # 获得对应知识点试题的总的url
            if period_sub not in subject_list:
                continue
            try:
                self._get_treeitem(start_url)
            except Exception as err:
                self.subject_err_f.write('%s:::%s\n' % (period_sub, start_url))
                self.subject_err_f.flush()
            if not self.url_list:
                continue
            for url_dict in self.url_list:
                [(title, url)] = url_dict.items()
                try:
                    self._get_all_ques(period_sub, title, url)
                except Exception as err:
                    self.know_err_f.write('%s:::%s:::%s\n' % (period_sub, title, url))
                    self.know_err_f.flush()

    def _del_error(self):
        self._err_img_down()


    def test_page(self):
        period_sub = '高中数学'
        title = '已知两角的正、余弦，求和、差角的余弦'
        url = 'http://zujuan.xkw.com/gzsx/zsd28514/'
        self._get_all_ques(period_sub, title, url)


def main():
    xueke = XueKe()
    xueke.run()
    # xueke._del_error()
    # xueke._err_all_page()
    # xueke.test_page()


if __name__ == '__main__':
    main()


