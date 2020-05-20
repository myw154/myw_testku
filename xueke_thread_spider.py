import requests
import re
import os
import json
import pdb
import hashlib
import threading
from copy import deepcopy
from retrying import retry
from lxml import etree
from bs4 import BeautifulSoup
from requests import request
from setting import SUBJECT_ID, START_URL, HEADERS, IMG_HEADERS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class XueKe(object):
    def __init__(self):
        self._gen_dir_path()
        self.start_url_list = START_URL.items()
        self.headers = HEADERS
        self.img_headers = IMG_HEADERS
        self.parse_img_url = 'http://im.zujuan.xkw.com/Parse/{}/{}/843/14/28/{}'
        self.anwer_img_url = 'http://im.zujuan.xkw.com/Answer/{}/{}/843/14/28/{}'
        self.form_data_set = set()
        self._init_form_data

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
        li_obj_list = html_obj.xpath('.//div[@id="treeContainer"]/ul/li')
        self.url_list = []
        self._parse_treeitme(li_obj_list)

    # 获得目录的最里层的url
    def _parse_treeitme(self, li_obj_list):
        for li_obj in li_obj_list:
            title = li_obj.xpath('./a/@title')[0]
            a_url = li_obj.xpath('./a/@href')[0]
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

    def _get_all_ques(self, period_sub, title, url, pager_err_f, img_err_f, form_file):
        res = self._send_request(url, self.headers)
        html_str = self._bytes_to_str(res)
        p_num = self._get_ques_pages(html_str)
        page_url = url+'qs-1o2p{}/'
        f_write = self._get_file_hand(period_sub[:2], period_sub[2:], title)
        for num in range(1, p_num+1):
            url = page_url.format(num)
            try:
                self._get_per_page(period_sub, url, f_write, img_err_f, form_file)
                print('%s:::%s:::第 %s 页:::已采集' % (period_sub, title, num))
            except Exception as err:
                page_err_f.write('%s:::%s:::%s\n' % (period_sub, title, url))

    # 获得每一页的试题
    def _get_per_page(self, period_sub, url, f_wr, img_err_f, form_file):
        hex_img = hashlib.md5(url.encode(encoding='UTF-8')).hexdigest()
        if hex_img in self.form_data_set:
            return
        res = self._send_request(url, self.headers)
        html_str = self._bytes_to_str(res)
        html_obj = etree.HTML(html_str)
        div_list = html_obj.xpath('.//div[@id="queslistbox"]/div')
        self._store_qus(period_sub, url, f_wr, div_list, hex_img, img_err_f, form_file)

    # 存储试题
    def _store_qus(self, period_sub, url, f_wr, div_list, hex_img, img_err_f, form_file):
        for div_obj in div_list:
            ques_dict = {}
            period = period_sub[:2] # 学段
            ques_dict['period'] = period
            subject = period_sub[2:] # 学科
            ques_dict['subject'] = subject
            sub_id = SUBJECT_ID[period_sub]
            ques_id = div_obj.xpath('./div[1]/@id')[0].replace('quesdiv', '') # 试题id
            ques_dict['source'] = ques_id
            img_key = div_obj.xpath('./div[1]/@key')[0]
            parser_img = self.parse_img_url.format(ques_id, sub_id, img_key) # 解析图片url
            answer_img = self.anwer_img_url.format(ques_id, sub_id, img_key) # 答案图片地址
            ques_dict['parser_img'] = parser_img
            ques_dict['answer_img'] = answer_img
            ques_dict['stem_str'] = etree.tostring(div_obj, encoding='utf-8').decode()
            f_wr.write(json.dumps(ques_dict, ensure_ascii=False)+'\n')
            f_wr.flush()
            self._down_img(parser_img, img_err_f)
            self._down_img(answer_img, img_err_f)
        form_file.write(hex_img+'\n')
        form_file.flush()

    # 图片下载
    def _down_img(self, img_url, img_err_f):
        try:
            res = self._send_request(img_url, headers=self.img_headers)
        except Exception as err:
            img_err_f.write(img_url+'\n')
            img_err_f.flush()
            return
        img_name = img_url.replace('/', '~~~').replace(':', '___')
        img_path = os.path.join(BASE_DIR, 'data/img',img_name+'.png')
        with open(img_path, 'wb') as f:
            f.write(res.content)

    # 获得总页数
    def _get_ques_pages(self, html_str):
        html_obj = etree.HTML(html_str)
        page_num = html_obj.xpath('.//a[@id="lastpage"]/@lastid')[0]
        p_num = int(page_num)
        return p_num

    '''
    def test_tree(self):
        for start_url in list(START_URL.values())[:1]:
            self._get_treeitem(start_url)
    
    '''
    '''
    所有科目
    ['小学语文', '小学数学', '小学英语', '小学科学', '小学道德与法治', '初中语文', '初中数学',
    '初中英语', '初中物理', '初 中化学', '初中生物', '初中地理', '初中道德与法治', '初中历史',
    '初中历史与社会', '初中科学', '初中信息技术', '高中语文', '高中数学', '高中英语', '高中物理',
    '高中化学', '高中生物', '高中政治', '高中历史', '高中地理', '高中信息技术', '高中通用技术']
    '''
    def process(self, sub_l, page_err_f, know_err_f, sub_err_f, img_err_f, form_file):
        for period_sub, start_url in self.start_url_list:
            # 获得对应知识点试题的总的url
            if period_sub not in sub_l:
                continue
            try:
                self._get_treeitem(start_url)
            except Exception as err:
                sub_err_f.write('%s:::%s\n' % (period_sub, start_url))
            if not self.url_list:
                continue
            for url_dict in self.url_list:
                [(title, url)] = url_dict.items()
                try:
                    self._get_all_ques(period_sub, title, url, img_err_f, form_file)
                except Exception as err:
                    know_err_f.write('%s:::%s:::%s\n' % (period_sub, title, url))

def main():
    xueke = XueKe()
    subject_l = ['小学语文', '小学数学', '小学英语', '小学科学', '小学道德与法治', '初中语文', '初中数学',
    '初中英语', '初中物理', '初 中化学', '初中生物', '初中地理', '初中道德与法治', '初中历史',
    '初中历史与社会', '初中科学', '初中信息技术', '高中语文', '高中数学', '高中英语', '高中物理',
    '高中化学', '高中生物', '高中政治', '高中历史', '高中地理', '高中信息技术', '高中通用技术']
    thread_list = []
    base_num = 7
    for i in range(len(subject_l)//base_num+1):
        sub_l = subject_l[i*base_num:(i+1)*base_num]

        page_err_f = open(os.path.join(BASE_DIR, 'log/page_err_thread_{}'.format(i)), 'a')
        know_err_f= open(os.path.join(BASE_DIR, 'log/know_page_err_thread_{}'.format(i)), 'a')
        subject_err_f = open(os.path.join(BASE_DIR, 'log/subject_err_thread_{}'.format(i)), 'a')
        img_err_f = open(os.path.join(BASE_DIR, 'log/img_err_thread_{}'.format(i)), 'a')
        form_file = open(os.path.join(BASE_DIR, 'log/form_data_fille_{}'.format(i)), 'a')

        parameter = (sub_l, page_err_f, know_err_f, subject_err_f, img_err_f, form_file)
        thread_list.append(threading.Thread(target=test.process, args=parameter))
    for thread in thread_list:
        thread.start()
    for thread in thread_list:
        thread.join()


if __name__ == '__main__':
    main()


