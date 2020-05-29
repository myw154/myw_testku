import os
import sys
import json
import re
import copy
import fitz
import requests
from lxml import etree
from retrying import retry
from requests import request

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# print(CURRENT_PATH)
class BaseAnanlys(object):

    def __init__(self):
        self.headers_dzkb = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'www.dzkbw.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
        }


    @retry(stop_max_attempt_number=5, stop_max_delay=3000, wait_fixed=3000, wait_incrementing_increment=500)
    def send_request(self, url, headers=None):
        requests.packages.urllib3.disable_warnings()
        res = request(method='get', url=url, headers=headers, timeout=10, verify=False)
        return res

    # 把字节转成字符串
    def bytes_to_html(self, html_bytes):
        try:
            html_obj = etree.HTML(html_bytes.conten.decode(encoding='utf-8'))
        except Exception:
            try:
                html_obj = etree.HTML(html_bytes.content.decode(encoding='gbk'))
            except Exception:
                try:
                    html_obj = etree.HTML(html_bytes.content.decode(encoding='GB2312'))
                except Exception:
                    html_obj = etree.HTML(html_bytes.content.decode(encoding='GB18030'))
        return html_obj

    def get_page_num(self, book_url):
        res = self.send_request(book_url, self.headers_dzkb)
        html_str = res.text
        page_num = int(re.search(r'maxPage=(\d+)', html_str).group(1))
        return page_num

    def read_already(self):
        with open(CURRENT_PATH+'/already.txt', 'r', encoding='utf-8') as f:
            book_all_str_list = f.readlines()
            book_list = []
            for book_str in book_all_str_list:
                book_dict = eval(book_str.replace('\n', ''))
                book_list.append(book_dict)
        return book_list

    def get_catalogs(self, book_url, chapter_list):
        # 构造目录目录
        catalogs = []
        n = len(chapter_list)
        for j in range(1, n):
            chapter = chapter_list[j - 1]
            start_num = int(chapter[0].split('/')[-1].replace('.htm', ''))
            end_num = int(chapter_list[j][0].split('/')[-1].replace('.htm', '')) - 1
            if end_num < start_num:
                catalogs.append({'name': chapter[1], 'url': chapter[0], 'pages': [start_num - 1, start_num - 1]})
            else:
                catalogs.append({'name': chapter[1], 'url': chapter[0], 'pages': [start_num - 1, end_num - 1]})
        chapter = chapter_list[-1]
        start_num = int(chapter[0].split('/')[-1].replace('.htm', ''))
        # 获得最大页码
        max_page_num = self.get_page_num(book_url)
        catalogs.append({'name': chapter[1], 'url': chapter[0], 'pages': [start_num - 1, max_page_num - 1]})
        return catalogs

    def get_book_all_chapter(self, book_name):
        pages_list = []
        with open(CURRENT_PATH + '/chapter_img_url.txt', 'r', encoding='utf-8') as f:
            img_str_list = set(f.readlines())
            for img_str in img_str_list:
                img_list = eval(img_str)
                # index = int(img_list[0].split('/')[-1].replace('.htm', ''))
                book_name_img = '_'.join(img_list[0].split('/')[3:-1])
                if book_name == book_name_img:
                    pages_list.append(img_list)
        pages_list.sort(key=lambda img_list: int(img_list[0].split('/')[-1].replace('.htm', '')))
        return pages_list

    def analys_chapter(self, book_list):
        for book_dict in book_list:
            # 一本书的名字
            book_name = '_'.join(book_dict['url_1'].split('/')[3:-1])
            primary_school = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
            junior_school = ['七年级', '八年级', '九年级']
            high_school = ['高一', '高二', '高三']
            grade_str = book_dict['grade'][:3]
            if grade_str in primary_school:
                book_dict['period'] = '小学'
            elif grade_str in junior_school:
                book_dict['period'] = '初中'
            elif grade_str in high_school:
                book_dict['period'] = '高中'
            book_dict['grade'] = grade_str
            # 构造catalongs
            book_url = book_dict['url_2']
            catalogs = self.get_catalogs(book_url, book_dict['new_chapter'])
            book_dict['catalogs'] = catalogs
            del book_dict['chapter']
            del book_dict['new_chapter']
            pages_list = self.get_book_all_chapter(book_name)
            book_dict['pages'] = []
            for j in pages_list:
                book_dict['pages'].append(j[1])
            print(json.dumps(book_dict, ensure_ascii=False), file=self.f_write, flush=True)
        self.f_write.close()

    def main(self):
        book_list = self.read_already()
        self.analys_chapter(book_list)

class BasePdf(object):
    def pdf(self):
        with open(os.path.join(CURRENT_PATH, 'yousi/new_already.json'), 'r', encoding='utf-8') as f:
            # f.write(json.dumps(book_info_dict, ensure_ascii=False) + '\n')
            book_info_str_list = f.readlines()
            for book_info_str in book_info_str_list:
                book_dict = {}
                book_dict['pages']=[]
                book_info_dict = eval(book_info_str)
                chapter_html_str = book_info_dict['chapter_html']
                html_obj = etree.HTML(chapter_html_str)
                basic_info = html_obj.xpath('.//div[@class="daohan"]/*/text()|.//div[@class="daohan"]/a//text()')
                if re.search('一年级|二年级|三年级|四年级|五年级|六年级', basic_info[3]):
                    book_dict['period'] = '小学'
                    book_dict['grade'] = re.search('一年级|二年级|三年级|四年级|五年级|六年级', basic_info[3]).group()
                elif re.search('七年级|八年级|九年级', basic_info[3]):
                    book_dict['period'] = '初中'
                    book_dict['grade'] = re.search('七年级|八年级|九年级', basic_info[3]).group()
                elif re.search('高一|高二|高三', basic_info[3]):
                    book_dict['period'] = '高中'
                    book_dict['grade'] = re.search('高一|高二|高三', basic_info[3]).group()
                book_dict['press_version'] = basic_info[1]
                book_dict['subject'] = basic_info[2]
                a_obj_list = html_obj.xpath('.//div[@class="bookmulu"]')[0]
                a_obj_str= etree.tostring(a_obj_list, encoding='utf-8').decode()
                #   self.get_chapter(a_obj_list)
                book_dict['catalogs'] = {'name': str(a_obj_str)}
                book_dict['pdf_url'] = book_info_dict['pdf_url']
                pdf_name = re.search('/(\d+\.pdf)', book_info_dict['pdf_url']).group(1)
                pdf_path = '/home/mengyanwei/myw_env/pdf/book_info/'+pdf_name
                doc = fitz.open(pdf_path)
                page_count = doc.pageCount
                for i in range(0, page_count):
                    img_name = pdf_name.replace('.pdf', '_{}.jpg').format(i)
                    book_dict['pages'].append(img_name)
                print(book_dict)
                with open(os.path.join(CURRENT_PATH+'/yousi/analys_already.json'), 'a', encoding='utf-8') as f:
                     f.write(json.dumps(book_dict, ensure_ascii=False)+'\n')
            #   a_obj_list = html_obj.xpath('.//div[@class="bookmulu"]//a')
            #   print(len(a_obj_list))
            #   self.get_chapter(a_obj_list)

    def get_chapter(self, a_obj_list):
        catalogs = []
        for a_obj in a_obj_list:
            if a_obj.xpath('./strong|./b'):
                name = a_obj.xpath('.//text()')
                if len(name) > 1:
                    son_catalogs = [{'name': name[1].replace('\u3000', ' '), 'pages': [], 'catalogs': []}]
                else:
                    son_catalogs = []
                href = a_obj.xpath('./@href')[0]
                start_num = int(href.split('/')[-1].replace('.htm', ''))
                catalogs.append({'name': name[0].replace('\u3000', ' '), 'pages': [start_num, ], 'catalogs': son_catalogs})

        # print(catalogs)

        index_list = []
        for big_chapter_dict in catalogs:
            i = 1
            for a_obj in a_obj_list:
                if a_obj.xpath('.//text()')[0].replace('\u3000', ' ') == big_chapter_dict['name']:
                    index_list.append(i)
                i += 1

        print(index_list)
        n = len(index_list)
        new_catalogs = copy.deepcopy(catalogs)
        for big_chapter_dict, index in zip(new_catalogs, range(n)):
            if index == 0:
                start_index = 0
                end_index = index_list[index]-1
                a_list = a_obj_list[start_index:end_index]
                if len(a_list) > 0:
                    for a_obj in a_list:
                        name = a_obj.xpath('.//text()')
                        if len(name) > 1:
                            son_catalogs = [{'name': name[1].replace('\u3000', ' '), 'pages': [], 'catalogs': []}]
                        else:
                            son_catalogs = []
                        href = a_obj.xpath('./@href')[0]
                        start_num = int(href.split('/')[-1].replace('.htm', ''))
                        catalogs.append({'name': name[0].replace('\u3000', ' '), 'pages': [start_num, ], 'catalogs': son_catalogs})

        # for big_chapter_dict in catalogs:
        #     for a_obj in a_obj_list:
        #         if a_obj.xpath('.//text()')[0].replace('\u3000', ' ') != big_chapter_dict['name']:
        #             name = a_obj.xpath('.//text()')
        #             if len(name) > 1:
        #                 big_chapter_dict['catalogs'].append({'name': name[0].replace('\u3000', ' '), 'pages': [], 'catalogs': []})
        #                 href = a_obj.xpath('./@href')[0]
        #                 start_num = int(href.split('/')[-1].replace('.htm', ''))
        #                 big_chapter_dict['catalogs'].append({'name': name[1].replace('\u3000', ' '), 'pages': [start_num], 'catalogs': []})
        #             else:
        #                 href = a_obj.xpath('./@href')[0]
        #                 start_num = int(href.split('/')[-1].replace('.htm', ''))
        #                 big_chapter_dict['catalogs'].append({'name': name[0].replace('\u3000', ' '), 'pages': [start_num], 'catalogs': []})
        #         elif a_obj.xpath('.//text()')[0].replace('\u3000', ' ') == big_chapter_dict['name']:
        #             break
        # for i in catalogs:
        #     print(i)

class Analys_100875(object):

    def read_info(self):
        with open(CURRENT_PATH+'/basic_net/already.txt', 'r', encoding='utf-8') as f:
            book_info_str_list = f.readlines()
            for book_info_str in book_info_str_list:
                book_dict = {}
                book_info_dict = eval(book_info_str)
                chapter_html_str = book_info_dict['chpater_html']
                html_obj = etree.HTML(chapter_html_str)
                basic_info = html_obj.xpath('.//div[@class="daohan"]/*/text()|.//div[@class="daohan"]/a//text()')
                if re.search('一年级|二年级|三年级|四年级|五年级|六年级', basic_info[3]):
                    book_dict['period'] = '小学'
                    book_dict['grade'] = re.search('一年级|二年级|三年级|四年级|五年级|六年级', basic_info[3]).group()
                elif re.search('七年级|八年级|九年级', basic_info[3]):
                    book_dict['period'] = '初中'
                    book_dict['grade'] = re.search('七年级|八年级|九年级', basic_info[3]).group()
                elif re.search('高一|高二|高三', basic_info[3]):
                    book_dict['period'] = '高中'
                    book_dict['grade'] = re.search('高一|高二|高三', basic_info[3]).group()
                book_dict['press_version'] = basic_info[1]
                book_dict['subject'] = basic_info[2]
                chapter_dict_list = book_info_dict["chapter"][0]
                # print(chapter_dict_list)
                new_chapter_list = []
                for pre_chpater_dict in chapter_dict_list:
                    if pre_chpater_dict['chapter_info'][0]['picture'] == 'wu':
                        new_chapter_list.append({'name': pre_chpater_dict['cataName']})
                    else:
                        new_chapter_list.append({'name':pre_chpater_dict['cataName'].replace('\u3000', ' '), 'pic_url':pre_chpater_dict['chapter_info'][0]['picture'],
                     'indexnum':pre_chpater_dict['chapter_info'][0]['indexNum'], 'totalnum':pre_chpater_dict['chapter_info'][0]['totalNum']})
                # print(new_chapter_list)
                book_dict['catalogs'] = new_chapter_list
                book_dict['pages'] = []
                if 'pic_url' in new_chapter_list[0]:
                    pic = new_chapter_list[0]['pic_url']
                    total_num = int(new_chapter_list[0]['totalnum'])
                    index_num = int(new_chapter_list[0]['indexnum'])
                    for i in range(index_num, total_num+1):
                        if i <= 9:
                            pic_new_url = pic[:-7]+'00{}.jpg'.format(i)
                        elif 10 <= i <= 99:
                            pic_new_url = pic[:-7]+'0{}.jpg'.format(i)
                        else:
                            pic_new_url = pic[:-7]+'{}.jpg'.format(i)
                        book_dict['pages'].append(pic_new_url)
                for dict_info in book_dict['catalogs']:
                    if 'pic_url' in dict_info:
                        del dict_info['pic_url']
                        del dict_info['indexnum']
                        del dict_info['totalnum']
                    dict_info['pages'] = []
                print(book_dict)
                with open(CURRENT_PATH+'/basic_net/analys_already.txt', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(book_dict, ensure_ascii=False)+'\n')
################################
    def read_info2(self):
        with open(CURRENT_PATH+'/basic_net/already.txt', 'r', encoding='utf-8') as f:
            book_info_str_list = f.readlines()
            for book_info_str in book_info_str_list:
                book_dict = {}
                book_info_dict = eval(book_info_str)
                book_dict['source_url'] = book_info_dict['url_2']
                chapter_html_str = book_info_dict['chpater_html']
                html_obj = etree.HTML(chapter_html_str)
                basic_info = html_obj.xpath('.//div[@class="daohan"]/*/text()|.//div[@class="daohan"]/a//text()')
                book_dict['book_name'] = '_'.join(basic_info)
                if re.search('一年级|二年级|三年级|四年级|五年级|六年级', basic_info[3]):
                    book_dict['period'] = '小学'
                    book_dict['grade'] = re.search('一年级|二年级|三年级|四年级|五年级|六年级', basic_info[3]).group()
                elif re.search('七年级|八年级|九年级', basic_info[3]):
                    book_dict['period'] = '初中'
                    book_dict['grade'] = re.search('七年级|八年级|九年级', basic_info[3]).group()
                elif re.search('高一|高二|高三', basic_info[3]):
                    book_dict['period'] = '高中'
                    book_dict['grade'] = re.search('高一|高二|高三', basic_info[3]).group()
                book_dict['press_version'] = basic_info[1]
                book_dict['subject'] = basic_info[2]
                chapter_dict_list = book_info_dict["chapter"][0]
                # print(chapter_dict_list)
                # print(len(chapter_dict_list))
                new_chapter_list = []
                for pre_chpater_dict in chapter_dict_list:
                    if pre_chpater_dict['chapter_info'][0]['picture'] == 'wu':
                        new_chapter_list.append({'name': pre_chpater_dict['cataName'].replace(r'\u2003', ' '), 'deep':pre_chpater_dict['deep'],'catalogs':[], 'pages':[]})
                    else:
                        new_chapter_list.append({'name':pre_chpater_dict['cataName'].replace('\u3000', ' ').replace(r'\u2003', ' '), 'deep':pre_chpater_dict['deep'], 'pic_url':pre_chpater_dict['chapter_info'][0]['picture'],
                     'indexnum':pre_chpater_dict['chapter_info'][0]['indexNum'], 'totalnum': pre_chpater_dict['chapter_info'][0]['totalNum'], 'catalogs':[]})
                # print(new_chapter_list)

                book_dict['catalogs'] = new_chapter_list
                book_dict['pages'] = []
                if 'pic_url' in new_chapter_list[0]:
                    pic = new_chapter_list[0]['pic_url']
                    total_num = int(new_chapter_list[0]['totalnum'])
                    index_num = int(new_chapter_list[0]['indexnum'])
                    for i in range(index_num, total_num+1):
                        if i <= 9:
                            pic_new_url = pic[:-7]+'00{}.jpg'.format(i)
                        elif 10 <= i <= 99:
                            pic_new_url = pic[:-7]+'0{}.jpg'.format(i)
                        else:
                            pic_new_url = pic[:-7]+'{}.jpg'.format(i)
                        book_dict['pages'].append(pic_new_url)
                for dict_info in book_dict['catalogs']:
                    if 'pic_url' in dict_info:
                        del dict_info['pic_url']
                        del dict_info['indexnum']
                        del dict_info['totalnum']
                    dict_info['pages'] = []
                # print(book_dict)
                # 找到大章节
                big_chapter_list = []
                n = len(book_dict['catalogs'])
                big_index_list = []
                for chapter_dict, i in zip(book_dict['catalogs'], range(1, n + 1)):
                    if chapter_dict['deep'] == '5':
                        del chapter_dict['deep']
                        big_chapter_list.append(chapter_dict)
                        big_index_list.append(i)
                big_index_list.append(n + 1)
                # print(big_chapter_list)

                m = len(big_index_list)
                for pre_big_dcit, j in zip(big_chapter_list, range(0, m)):
                    for little_chaper in book_dict['catalogs'][big_index_list[j]:big_index_list[j + 1] - 1]:
                        del little_chaper['deep']
                        pre_big_dcit['catalogs'].append(little_chaper)
                if big_chapter_list:
                    book_dict['catalogs'] = big_chapter_list
                    print(book_dict)
                    with open(CURRENT_PATH + '/basic_net/analys_already.txt', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(book_dict, ensure_ascii=False)+'\n')
                else:
                    print(book_dict)
                    with open(CURRENT_PATH + '/basic_net/analys_already.txt', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(book_dict, ensure_ascii=False)+'\n')

if __name__ == '__main__':
    base_analy = BaseAnanlys()
    # base_analy.main()
    #basepdf = BasePdf()
    #basepdf.pdf()
    analys_10875 = Analys_100875()
    analys_10875.read_info2()
