import re
import requests
import time
import os
import indject_js_proxy
import img_canndy
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from PIL import Image
from six import BytesIO
from selenium.webdriver import ActionChains

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class login_model:
    def __init__(self):
        self.login_url = 'https://account.weimob.com/login.html'
        self.user_url = 'https://master.weimob.com/app/retail/100001433687/2401135687/goods/management/goodslist'
        self.host_url = "https://captcha.guard.qcloud.com"
        self.headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36"}
        # 初始化浏览器
        self.browser = self._init_driver()

    def move_to_gap(self, slider, tracks):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param tracks: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in tracks:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def close_page(self):
        self.browser.quit()

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为正 2
                a = 4
            else:
                # 加速度为负 3
                a = -2
            # 初速度 v0
            v0 = v
            # 当前速度 v = v0 + at
            v = v0 + a * t
            # 移动距离 x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument(self.headers['User-Agent'])
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-infobars')
        # 自动化测试提醒
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # linux下对配置与无头
        # options.add_argument('--single-process')
        # options.add_argument('--headless')
        options.add_argument('--disk-cache-size=12428800')
        browser = webdriver.Chrome(options=options)
        browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{
            "source":indject_js_proxy.injected_javascript
        })
        browser.implicitly_wait(5)
        return browser

    def into_login(self):
        # import pdb
        # pdb.set_trace()
        # 进入登陆页面
        self.browser.get(self.login_url)
        # 最大化
        self.browser.maximize_window()
        # 初始化等待时间
        wait = WebDriverWait(self.browser,10)
        # 等待页面元素
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#loginForm')))
        # 点击跳转登陆
        # user_pass_click = self.browser.find_element_by_css_selector('#loginForm > div > div.login-method__tab.J_LoginTab > ul > li.login-method__tab--ac.tab')
        # user_pass_click.click()
        
    def begin_login(self, user, password):
        """
        开始登陆
        """
        time.sleep(2)
        user_input = self.browser.find_element_by_id('phone') # 账号
        pwd_input = self.browser.find_element_by_id('pwd')  # 密码
        btn = self.browser.find_element_by_css_selector('#loginForm > div.ui-form-btn > input')  # 登陆按钮
        # 清空文本库
        user_input.clear()
        pwd_input.clear()
        # 写入账号密码
        user_input.send_keys(user)
        time.sleep(2)
        pwd_input.send_keys(password)
        time.sleep(2)
        btn.click()

    def get_ori_img(self):
        """
        获取源图片
        """
        # 获取滑块对iframe
        iframe = WebDriverWait(self.browser, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > iframe')))
        iframe = self.browser.find_element_by_css_selector('body > iframe')
        # 焦点转入iframe
        self.browser.switch_to_frame(iframe)
        pageSource = self.browser.page_source
        img_1_re = re.compile(r'<img id="slideBkg" class="big img" style="visibility: .*?;" src="(.*?)">')
        img_2_re = re.compile(r'<img id="slideBlock" class="slideBlock" style="visibility: .*?;" src="(.*?)">')
        img_1 = self.host_url + img_1_re.findall(pageSource)[0]
        img_2 = self.host_url + img_2_re.findall(pageSource)[0]
        img_1 = img_1.replace('amp;', "")
        img_2 = img_2.replace('amp;', "")
        with open(BASE_DIR + "/img.png", "wb") as f:
            r = requests.get(img_1, headers=self.headers)
            f.write(r.content)
        with open(BASE_DIR + "/img_2.png", "wb") as f:
            r = requests.get(img_2, headers=self.headers)
            f.write(r.content)

    def get_sentence(self):
        """
        获取滑块距离
        """
        move = img_canndy.matchImg(BASE_DIR + "/img.png", BASE_DIR + "/img_2.png")
        distance = int(move[0] / 2) + random.choices([-2,-1,0,1,2])[0]
        return distance

    def very_login(self):
        """
        验证登陆
        """
        time.sleep(3)
        # 返回主页面
        self.browser.switch_to.default_content()
        # 判断拼图是否存在
        try:
            iframe = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'body > iframe')))
            # 跳转焦点
            self.browser.switch_to_frame(iframe)
            # 刷新当前iframe
            close_button = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#reload')))
            close_button.click()
            # self.browser.switch_to.default_content()
            return "jigsaw_error"
        except Exception as e:
            pass
        # 账号密码是否正确
        try:
            login_tips = self.browser.find_element_by_css_selector("#messageBox").text
            if "手机号或密码错误" in login_tips:
                print(login_tips)
                return "passwd_error"
            # if "因频繁密码错误已被锁定" in login_tips:
                # print(login_tips)
                # return "passwd_lock"
        except:
            pass

        return self.login_is_succ()

    def login_is_succ(self):
        """
        判断页面是否跳转
        """
        local_url = self.browser.current_url
        if local_url != self.login_url:
            # if "安全验证" in self.browser.page_source:
                # return "security"
            return True

    
    def get_username(self):
        """
        得到当前模块名称
        """
        # 获取user_name
        # user_diver = browser.find_element_by_css_selector('body > div.g-cw1.cfx > div.w > div > div.user-info.cfx > div.user-message-wrap.fl > h1')
        sign = 0
        user_name = ""
        while True:
            try:
                user_diver =  WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#saas-fe-frame > div > div.saas-right > div.saas-fe-console-layout > div > div.saas-title')))
                user_name = user_diver.text
                break
            except:
                if sign:
                    break
                self.browser.get(self.user_url)
                sign += 1
        return user_name


    def get_cookie(self):
        '''
        获取当前登陆cookie，并拼接为字符串
        '''
        cookie_items = self.browser.get_cookies()
        cookie_str = ""
        #组装cookie字符串
        for item_cookie in cookie_items:
            item_str = item_cookie["name"]+"="+item_cookie["value"]+"; "
            cookie_str += item_str
        return cookie_str

    def run(self, user, password):
        # 进入login页面，并初始化浏览器
        self.into_login()
        try_num = 0
        while True:
            # 开始登陆
            self.begin_login(user, password)
            # 判断是否需要滑块
            if self.login_is_succ():
                break
            time.sleep(2)
            # 处理滑块
            sign = False
            while True:
                # 获取源图片
                self.get_ori_img()
                # 获取距离
                left = self.get_sentence()
                slide_btn = self.browser.find_element_by_css_selector('#slide_bar_head') #获取滑动按钮
                track = self.get_track(left) #获取滑动的轨迹
                self.move_to_gap(slide_btn, track) #进行滑动
                sign = self.very_login() # 验证登陆
                if sign == "jigsaw_error":
                    try_num += 1
                    if try_num > 3:
                        return "slider_error"
                    continue
                if sign == "passwd_error":
                    return sign
                if sign == True:
                    break
            if sign == True:
                break
        # 得到模块名称
        user_name = self.get_username()
        print(user_name)
        if user_name:
            cookie_str = self.get_cookie()
            return cookie_str
        else:
            return False

if __name__ == '__main__':
    login = login_model()
    # sign = login.run('18736141159','myw425425')
    sign = login.run('15010887481','myw123456')
    login.close_page()
    if sign == "passwd_error":
        print("密码错误")
    elif sign == "slider_error":
        print("滑块超过最大重试次数，请查看")
    elif sign == False:
        print("用户名获取失败，登陆失败")
    else:
        print(sign)
        print("登陆成功")


    # success = browser.find_element_by_css_selector('.geetest_success_radar_tip') #获取显示结果的标签
    # time.sleep(2)
    # if success.text == "验证成功":
    #     login_btn = browser.find_element_by_css_selector('button.j-login-btn') #如果验证成功，则点击登录按钮
    #     login_btn.click()
    # else:
    #     print(success.text)
    #     print('失败')

