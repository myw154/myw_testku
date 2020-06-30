import requests
import time
import json
from retrying import retry
from copy import deepcopy
from lxml import etree
from requests import request
from bs4 import BeautifulSoup

class ShiWen(object):
    def __init__(self):
        self.start_url_list =[
            'https://so.gushiwen.org/gushi/chuzhong.aspx','https://so.gushiwen.org/gushi/gaozhong.aspx',
            'https://so.gushiwen.org/wenyan/chuwen.aspx','https://so.gushiwen.org/wenyan/gaowen.aspx',
        ]
        self.header = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
        }

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

    def get_per_url(self):
        for start_url in self.start_url_list:
            if 'chu' in start_url:
                if '/gushi/' in start_url:
                    info_dict = {'period':'初中', 'type':'古诗'}
                else:
                    info_dict = {'period':'初中', 'type':'文言文'}
            else:
                if '/gushi/' in start_url:
                    info_dict = {'period':'高中', 'type':'古诗'}
                else:
                    info_dict = {'period':'高中', 'type':'文言文'}
            res = self._send_request(start_url, self.header)
            html_str = self._bytes_to_str(res)
            html_obj = etree.HTML(html_str)
            url_obj_list = html_obj.xpath('.//div[@class="main3"]//div[@class="typecont"]')
            for url_obj in url_obj_list:
                new_info_dict = deepcopy(info_dict)
                new_info_dict['grade']= url_obj.xpath('.//strong/text()')[0]
                url_a_list = url_obj.xpath('.//a')
                for url_a_obj in url_a_list:
                    new_info_dict['title'] = url_a_obj.xpath('./text()')[0]
                    new_info_dict['url'] = url_a_obj.xpath('./@href')[0] if url_a_obj.xpath('./@href') else None
                    with open('article_url', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(new_info_dict, ensure_ascii=False)+'\n')
                        print(json.dumps(new_info_dict, ensure_ascii=False))

    def get_article(self):
        i = 0
        with open('article_url', 'r', encoding='utf-8') as f:
            for info_str in f:
                info_dict = json.loads(info_str.strip())
                article_url = info_dict['url']
                if article_url:
                    res = self._send_request(article_url, self.header)
                    # import pdb
                    # pdb.set_trace()
                    html_str = self._bytes_to_str(res)
                    article_obj = etree.HTML(html_str).xpath('.//div[@class="main3"]/div[@class="left"]')[0]
                    arti_str =  etree.tostring(article_obj, encoding='utf-8').decode('utf-8')
                    info_dict['html_str'] = arti_str
                    with open('content_info', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(info_dict, ensure_ascii=False)+'\n')
                    print(json.dumps(info_dict, ensure_ascii=False))
                    i += 1
                    print('第%s 篇采集完成' % i)

    def _del_no_html(self, art_str):
        soup = BeautifulSoup(art_str, 'lxml')
        html_str = ''
        for tag_child in soup.find('div').children:
            if '猜您喜欢' in str(tag_child):
                break
            elif str(tag_child) == '\n':
                pass
            else:
                html_str += str(tag_child)
        return html_str

    def _rm_last_br(self, str_):
        str_ = str_.strip()
        if str_.startswith('<br/>'):
            str_ = str_[5:]
        elif str_.endswith('<br/>'):
            str_ = str_[:-5]
        return str_

    def _circle_con(self, tag):
        con_str = ''
        for child in tag.children:
            if isinstance(child, str):
                con_str += str(child)
            elif child.name == 'br':
                con_str += str(child)
            elif child.name == 'p':
                con_str += self._circle_con(child)
                con_str += '<br/>'
            else:
                con_str += self._circle_con(child)
        return con_str


    def _parse_content(self, info_dict, art_str):
        soup = BeautifulSoup(art_str, 'lxml')
        html_str = ''
        tag_obj = soup.find_all('div')[1]
        div_obj = tag_obj.find('div', class_="cont")
        title = div_obj.find('h1').string
        year_obj = div_obj.find('p', recursive=False)
        year_str = self._circle_con(year_obj)
        con_obj = div_obj.find('div', class_="contson")
        con_str = self._circle_con(con_obj)
        info_dict['title'] = title
        info_dict['year'] = year_str.split('：')[0].strip()
        info_dict['author'] = year_str.split('：')[1].strip()
        info_dict['content'] = self._rm_last_br(con_str)
        del info_dict['html_str']
        print(info_dict)


    def parse_article(self):
        with open('content_info', 'r', encoding='utf-8') as f:
            for info_str in f:
                info_dict = json.loads(info_str.strip())
                art_str = info_dict['html_str']
                art_str = self._del_no_html(art_str)
                self._parse_content(info_dict, art_str)


    def run(self):
        # 获取每篇文章的地址
        # self.get_per_url()
        # 获取每篇文章的内容
        # self.get_article()
        # 解析文章字符串
        self.parse_article()


print('jasldjflk')

def main():
    shiwen = ShiWen()
    shiwen.run()

if __name__ == '__main__':
    main()





