import requests
import os
import json
from retrying import retry
from requests import request
from lxml import etree
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class FengMian(object):
    def __init__(self):
        self.headers = {
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
        }

    @retry(stop_max_attempt_number=6, stop_max_delay=3000, wait_fixed=3000, wait_incrementing_increment=500)
    def send_rquest(self, url):
        requests.packages.urllib3.disable_warnings()
        res = request(method='get', url=url, headers=self.headers, timeout=10)
        try:
            html_str = res.content.decode(encoding='GBK')
        except:
            try:
                html_str = res.content.decode(encoding='utf-8')
            except:
                try:
                    html_str = res.content.decode(encoding='GB2312')
                except:
                    html_str = res.content.decode(encoding='GB18030')

        return html_str

    def add_fengmian(self):
        with open(os.path.join(BASE_PATH, 'book_url.txt'), 'r', encoding='utf-8') as f:
            fengmian_list = f.readlines()
        with open(os.path.join(BASE_PATH, 'repair_img_url.json'), 'r', encoding='utf-8') as f:
            info_dict_list = f.readlines()
        i = 0
        for info_dict_str in info_dict_list:
            info_dict = json.loads(info_dict_str)
            if 'source_url' in info_dict:
                try:
                    print(info_dict['source_url'])
                    if info_dict['source_url'].startswith('http://www.dzkbw.com'):
                        for fengmian_str in fengmian_list:
                            all_url_list = eval(fengmian_str)
                            if info_dict['source_url'] == all_url_list[1]:
                                print(all_url_list[0])
                                html_str = self.send_rquest(url=all_url_list[0].replace('\n', ''))
                                html_obj = etree.HTML(html_str)
                                fengmian_url = html_obj.xpath('.//div[@class="bookmulu"]/img/@src')[0]
                                print(fengmian_url)
                                info_dict['profile_url'] = fengmian_url
                                with open(os.path.join(BASE_PATH, 'profile_url.txt'), 'a', encoding='utf-8') as f:
                                    f.write(fengmian_url+'\n')
                                info_dict['source_url_1'] = all_url_list[0].replace('\n', '')
                    elif info_dict['source_url'].startswith('https://xuezi5.com/'):
                        html_str = self.send_rquest(url=info_dict['source_url'])
                        html_obj = etree.HTML(html_str)
                        fengmian_url = html_obj.xpath('.//div[@class="conlist"]/div[@class="pic"]/img/@src')[0] if len(html_obj.xpath('.//div[@class="conlist"]/div[@class="pic"]/img/@src')) > 0 else None
                        info_dict['profile_url'] = fengmian_url
                    else:
                        info_dict['profile_url'] = None
                except Exception:
                    with open(os.path.join(BASE_PATH, 'error_profile.txt'), 'a', encoding='utf-8') as f:
                        f.write(json.dumps(info_dict,ensure_ascii=False)+'\n')
            else:
                info_dict['profile_url'] = None
            with open(os.path.join(BASE_PATH, 'repair_img_profile_url.json'), 'a', encoding='utf-8') as f:
                f.write(json.dumps(info_dict, ensure_ascii=False)+'\n')
            i+=1
            print(i)

def main():
    fengmian = FengMian()
    fengmian.add_fengmian()

if __name__ == '__main__':
    main()
