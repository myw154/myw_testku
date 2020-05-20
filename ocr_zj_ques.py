#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
file:    ocr_zj_ques.py
author:  songzitao@iyunxiao.com
date:    2018/03/22
brief:   recognizing question's text by ocr
"""

import sys
import time
import json
import base64
import urllib
import requests
import threading
import urllib.request
from io import BytesIO
from PIL import Image
from queue import Queue
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict

#import TencentYoutuyun
import pymongo
from pymongo import UpdateOne


class OCRQues(object):
    '''recognise ques's img
    '''
    def __init__(self, logger, db, thread_ocr_num=2, bulk_size=100, test=False, debug=False):
        self.db = db
        self.logger = logger
        self.debug = debug
        self.test = test
        self.thread_ocr_num = thread_ocr_num
        self.bulk_size = bulk_size
        self.leagal_type = ['explanations', 'answers', 'knowledges']
        self.maxsize = thread_ocr_num * 4 # 队列最大容量
        self.ques_q = Queue(self.maxsize)
        self.res_q = Queue(self.maxsize)
        self.lock_ = threading.Lock()

        self.result_none = 0
        self.print_ocr_none = 0

        self.producer_list = []
        self.result_l = []
        self.request = []
        self.f_producer_count = {}    # 失败生产者重新加入队列统计


        #self._init_ocr()

        if not self.test:
            self.coll = self.db.zj_question
        else:
            self.coll = self.db.test_zj_question
        #self.youtu = self._init_ocr()
        # 统计报告
        self.count = 0 # ocr试题总数
        self.suc_count = 0 # ocr成功图片数
        self.err_count = 0 # ocr异常图片数

    def _init_ocr(self):
        self.appid = '10124458'
        secret_id = 'AKIDJWyEPpoB6qRr8vc6PaaQ4au353qT89C4'
        secret_key = 'pStAORK1Wt44shMp7VmrkliYFoT2Tjng'
        userid = '309050696'

        end_point = TencentYoutuyun.conf.API_YOUTU_END_POINT
        youtu = TencentYoutuyun.YouTu(self.appid, secret_id, secret_key, userid, end_point)
        return youtu

    def _deal_image_d(self, field, field_type, ques_id, subject):
        '''生产者列表填充
        '''
        assert(field_type in self.leagal_type)

        for index, image_url in enumerate(field):
            item = (ques_id, field_type, index, subject, image_url)
            self.producer_list.append(item)

    def _deal_image_d_supply(self, field, field_type, ques_id,
                             subject, ori_field):
        '''生产者列表填充
        '''
        assert(field_type in self.leagal_type)

        if len(ori_field) < len(field):
            for i in range(len(field)-len(ori_field)):
                ori_field.append('')
        for index, image_url in enumerate(field):
            ori_content = ori_field[index]
            if not ori_content:
                item = (ques_id, field_type, index, subject, image_url)
                self.producer_list.append(item)

    def _deal_one_data(self, data):
        try:
            ques_id = data['_id']
            source_url = data['source_url']
            subject = data['subject']
            knowledges_img = data['knowledges_img']
            knowledges = data['knowledges']
            blocks = data['blocks']
            explanations_img = blocks['explanations_img']
            explanations = blocks['explanations']
            answers = blocks['answers']
            answers_img = blocks['answers_img']

            #self._deal_image_d(explanations_img, 'explanations',
            #                   ques_id, subject)
            #self._deal_image_d(answers_img, 'answers', ques_id, subject)
            #self._deal_image_d(knowledges_img, 'knowledges', ques_id, subject)

            self._deal_image_d_supply(explanations_img, 'explanations',
                                      ques_id, subject, explanations)
            self._deal_image_d_supply(answers_img, 'answers', ques_id,
                                      subject, answers)
            self._deal_image_d_supply(knowledges_img, 'knowledges', ques_id,
                                      subject, knowledges)

        except Exception as err:
            raise Exception('_deal_one_data:%s:%s' % (source_url, err))

    def _thread_producer(self):
        for item in self.producer_list:
            # 生产者加入
            while True:
                if self.ques_q.qsize() < self.thread_ocr_num * 2:
                    self.ques_q.put(item)
                    break
                else:
                    time.sleep(0.05)

        None_list = [None] * self.thread_ocr_num
        for item in None_list:
            self.ques_q.put(item)

    def _creat_ocr_result(self, query, List):
        result = {}
        result['id'] = List[0]
        result['query'] = query
        result['field_type'] = List[1]
        result['subject'] = List[3]
        result['index'] = List[2]
        result['image_url'] = List[4]
        return result

    def _fail_producer_count(self, image_url):
        '''失败图片统计
        '''
        if image_url not in self.f_producer_count:
            self.f_producer_count[image_url] = 1
        else:
            self.f_producer_count[image_url] += 1

    def _deal_recog_fail(self, List):
        '''识别失败的图片重新加入生产者队列
        '''
        ques_id = List[0]
        image_url = List[4]
        self._fail_producer_count(image_url)
        # 如果识别失败的case加入生产者次数小于3次
        if self.f_producer_count[image_url] < 3:
            if self.ques_q.qsize() >= self.maxsize:
                self.producer_list.append(List)
            else:
                self.ques_q.put(List)
            self.logger.error('%s:into producer' % (image_url))
        else:
            fail_result = self._creat_ocr_result('', List)
            self.res_q.put(fail_result)
            self.logger.error('_id::%s::%s::ocr over times' %
                              (ques_id, image_url))

    def _read_tencent(self, data):
        items = data['items']
        str_ = ''
        for item_d in items:
            itemstring = item_d['itemstring'].encode('iso8859-1').decode('utf-8')
            str_ += itemstring
        return str_
    
    def _bd_ocr(self, image_url, params):
        try:
            #image_quote = urllib.request.quote(image_url.encode('utf-8'))
            #params['image_url'] = image_quote
            params['api_key'] = 'iyunxiao_tester'
            params_encode = urllib.parse.urlencode(params)
            url = 'http://kb.yunxiao.com/ocr_api/v2/images/quality?' + params_encode
            file_ = urllib.request.urlopen(image_url, timeout=30)
            content = file_.read()
            files = {'file': content}
            handle = requests.post(url, files=files)
            file_.close()

            res = handle.json()

            if not res:
                raise Exception('Error: _fetch_url: [%s] res is null' % (url))

            if res['code'] != 0:
                raise Exception('Error: _fetch_url: [%s] res code is not 0'
                                % (url))
        except Exception as err:
            raise Exception('_bd_ocr:%s' % err)
        else:
            query = res['data']
            return query 

    def _yunxiao_ocr(self, image_url, params):
        try:
            params['image_url'] = image_url
            params['api_key'] = 'iyunxiao_tester'
            url = 'http://kb.yunxiao.com/ocr_api/v2/images'
            handle = requests.get(url, params=params)

            res = handle.json()

            if not res:
                raise Exception('Error: _fetch_url: [%s] res is null' % (url))

            if res['code'] != 0:
                raise Exception('Error: _fetch_url: [%s] res code is not 0'
                                % (url))
        except Exception as err:
            raise Exception('_yunxiao_ocr:%s' % err)
        else:
            query = res['data']
            return query 

    def _tencent_ocr(self, image_url, content_is_null=False):
        try:
            req_type='generalocr'
            headers = self.youtu.get_headers(req_type)
            url = self.youtu.generate_res_url(req_type, 2)
            data = {
                "app_id": self.appid,
                "session_id": '',
            }

            res = urllib.request.urlopen(image_url).read()
            img = Image.open(BytesIO(res))

            wh_str = image_url.split('@')[1]
            w = wh_str.split('&')[0].split('=')[1] 
            h = wh_str.split('&')[1].split('=')[1] 
            w = int(w)
            h = int(h)
            if content_is_null:
                out = img.resize((w, h), Image.ANTIALIAS)
                o = BytesIO()
                out.save(o, 'png', quality=80)
                out.close()
            else:
                o = BytesIO()
                img.save(o, 'png', quality=80)
            data['image'] = base64.b64encode(o.getvalue()).rstrip().decode('utf-8')
            img.close()

            r = requests.post(url, headers=headers, data=json.dumps(data))
            if r.status_code != 200:
                raise Exception('''{'httpcode': %s, 'errorcode':'', 'errormsg':''}''' % r.status_code)

            ret = r.json()
            str_ = self._read_tencent(ret) 
        except Exception as err:
            raise Exception('_tencent_ocr:%s' % (err))
        else:
            return str_

    def _fetch_url(self, url, retry_times, params):
        '''识别后内容提取
        '''
        for i in range(retry_times):
            try:
                str_ = self._yunxiao_ocr(url, params)  
            except Exception as err:
                self.logger.error('_fetch_url:%s:%s' % (url, err))
                continue
            else:
                self.suc_count += 1
                return str_
        
        self.err_count += 1
        raise Exception('Error: over retry times: %s' % (url))

    def _image_url_recog(self, image_url, subject):
        '''对image_url进行识别返回识别内容
        '''
        try:
            params = {
                'api_key': 'iyunxiao_tester'
            }
            if subject == '科学':
                subject = '物理'
            params['subject'] = subject
            res = self._fetch_url(image_url, 1, params)
        except Exception as err:
            raise err
        else:
            return res

    def _thread_consumer(self, params):
        '''ocr消费者
        '''
        while True:
            List = self.ques_q.get()
            try:
                if not List:
                    self.print_ocr_none += 1
                    if self.print_ocr_none <= self.thread_ocr_num:
                        self.res_q.put(None)
                    self.ques_q.task_done()
                    break
                else:
                    subject = List[3]
                    image_url = List[4]
            except Exception as err:
                self.ques_q.task_done()
                continue
            try:
                query = self._image_url_recog(image_url, subject)
            except Exception as err:
                self._deal_recog_fail(List)
                self.ques_q.task_done()
            else:
                result = self._creat_ocr_result(query, List)
                self.res_q.put(result)
                self.ques_q.task_done()

    def _merge_result(self):
        '''合并同一题的识别数据
        '''
        result_d = defaultdict(list)
        for res in self.result_l:
            ques_id = res['id']
            result_d[ques_id].append(res)
        self.result_l = []
        return result_d

    def _detail(self, target_field, target_index, query):
        '''填充识别内容
        '''
        try:
            #for index, text_d in enumerate(target_field):
            #    if index == target_index:
            #        text_d['text'] = query
            #    else: pass
            #    target_field[index] = text_d
            if target_field == 'knowledges':
                target_field = query.split(';')
            else:
                if len(target_field) == 1 and isinstance(target_field[0], list):
                    try:
                        target_field[0][target_index] = query
                    except Exception:
                        target_field[0].append(query)
                else:
                    target_field[target_index] = query

        except Exception as err:
            raise Exception('_detail:%s:%s:%s:%s' % (err, target_field, target_index, query))
        else:
            return target_field

    def _merge_update_data(self, res_d, blocks, knowledges):
        '''合并待更新的数据
        '''
        try:
            utime = datetime.now()
            target_index = res_d['index']
            query = res_d['query']
            field_type = res_d['field_type']
            if field_type in blocks:
                target_field = blocks[field_type]
                blocks[field_type] = self._detail(target_field, target_index,
                                                  query)
            else:
                target_field = knowledges
                knowledges = self._detail('knowledges', target_index, query)

            update_data = {}
            update_data['blocks'] = blocks
            if knowledges:
                update_data['knowledges'] = knowledges
            update_data['utime'] = utime
            update_data['status'] = 'recognized'
        except Exception as err:
            raise Exception('_merge_update_data:%s' % err)
        else:
            return update_data

    def _update_data(self):
        '''更新具体逻辑
        '''
        try:
            result_d = self._merge_result()
            ques_ids = list(result_d.keys())
            filter_ = {"_id": {"$in":ques_ids}}
            projection = {"blocks":1, "knowledges":1, "source_url":1}
            cursor = self.coll.find(filter_, projection)
            for data in cursor:
                try:
                    ques_id = data['_id']
                    knowledges = data['knowledges']
                    blocks = data['blocks']

                    res_l = result_d[ques_id]
                    for res_d in res_l:
                        update_data = self._merge_update_data(res_d, blocks, knowledges)
                    up_filter = {"_id":ques_id}
                    up_projection = {"$set":update_data}
                    update_one = UpdateOne(up_filter, up_projection)
                    self.count += 1
                    self.request.append(update_one)
                except Exception as err:
                    self.logger.error('_update_one:%s:%s' % (err, ques_id))
                    continue
                else:
                    self.logger.info('_update_one_success:%s' % ques_id)
                if len(self.request) >= self.bulk_size:
                    self.coll.bulk_write(self.request)
                    self.logger.info('%s:%s' % (time.ctime(), self.count))
                    sys.stdout.flush()
                    self.request = []
        except Exception as err:
            raise Exception('_update_data:%s' % err)

    def _thread_update(self):
        '''更新线程
        '''
        while True:
            try:
                with self.lock_:
                    result = self.res_q.get()
                    if not result:
                        self.result_none += 1
                        if self.result_none == self.thread_ocr_num:
                            self.res_q.task_done()
                            break
                        else: pass
                    else:
                        if len(self.result_l) < self.bulk_size:
                            self.result_l.append(result)
                        else:
                            self._update_data()
            except Exception as err:
                raise Exception('_thread_update:%s' % err)

    def _ocr(self):
        '''ocr识别多线程文本
        '''
        params = {
            'api_key': 'iyunxiao_tester'
        }
        threads = []
        t = threading.Thread(target=self._thread_producer, args=())
        t.setDaemon(True)
        t.start()
        threads.append(t)

        for i in range(self.thread_ocr_num):
            t = threading.Thread(target=self._thread_consumer, args=(params, ))
            t.setDaemon(True)
            t.start()
            threads.append(t)

        t = threading.Thread(target=self._thread_update, args=())
        t.setDaemon(True)
        t.start()
        threads.append(t)

        for thread in threads:
            thread.join()

        if len(self.result_l) > 0:
            self._update_data()
        if len(self.request) > 0:
            self.coll.bulk_write(self.request)
            self.logger.info('%s:%s' % (time.ctime(), self.count))
            sys.stdout.flush()
            self.request = []

    def process(self):
        '''总体处理流程
        '''
        try:
            interval_date = datetime.now() - timedelta(days=1)
            if not self.debug:
                filter_ = {'ctime':{'$gt':interval_date}, 'status': 'increased'}
            else:
                from conf.settings_debug import DEBUG_IDS
                filter_ = {'_id': {'$in': DEBUG_IDS}}
            projection = {"subject":1, "blocks":1, "knowledges_img":1,
                          "source_url":1, "knowledges":1}
            cursor = self.coll.find(filter_, projection)
            for data in cursor:
                self._deal_one_data(data)

            self._ocr()
        except Exception as err:
            raise Exception('process:%s' % err)
