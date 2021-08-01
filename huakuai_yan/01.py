from selenium.webdriver import ActionChains
from selenium import webdriver
import time
import numpy as np
import requests
import cv2
        
def download_img(url,filename):
    r = requests.get(url)
    with open( filename + '.png', 'wb') as f:
        f.write(r.content)
#        print(filename + '下载完成')

def loginweb():
    global driver
    url = 'https://www.bmlink.com/entry/login.aspx'
    username='MLY2009LDHB'
    password='M9@Q6g7zqXWezpx'
    driver=webdriver.Chrome()
    driver.maximize_window() 
    driver.get(url=url)
    driver.find_element_by_id('pc').click()
    driver.find_element_by_id('userName').send_keys(username)
    driver.find_element_by_id('passwd1').send_keys(password)  
    huadong = driver.find_element_by_xpath('//*[@id="captcha_div2"]/div/div[2]/div[2]')
    time.sleep(0.5)
    moveyanzheng(huadong)
    
def moveyanzheng(huadong):    
    newact =  ActionChains(driver)
    newact.click_and_hold(huadong)
    time.sleep(0.5)
    bk = driver.find_element_by_xpath('//*[@id="captcha_div2"]/div/div[1]/div/div[1]/img[1]').get_attribute('src')
#    print(bk)
    key = driver.find_element_by_xpath('//*[@id="captcha_div2"]/div/div[1]/div/div[1]/img[2]').get_attribute('src')
#    print(key)
    download_img(bk,filename= 'bk')
    download_img(key,filename= 'key')
    dis = get_distance()
    print('滑动距离：{}'.format(dis))
    time.sleep(0.5)
    newact.move_by_offset(xoffset=dis+15,yoffset=0)
    time.sleep(0.5)
    newact.release().perform()
    time.sleep(1)
    huadongtext = driver.find_element_by_xpath('//*[@id="captcha_div2"]/div/div[2]/div[3]/span[2]').text
    if huadongtext == '向右拖动滑块填充拼图' or huadongtext == '加载中...' :
        time.sleep(0.5)
        moveyanzheng(huadong)
    else :
        driver.find_element_by_xpath('//*[@id="btn1"]').click()
    
#处理得到滑块应移动的距离。
def get_distance():
    # 读取两张图片
    slider_pic = cv2.imread('key.png', 0)
    background_pic = cv2.imread('bk.png', 0)


    imgContour = background_pic.copy()
    width, height = background_pic.shape[::-1]
#    print(width,height)
    slider01 = "slider01.jpg"
    background_01 = "background01.jpg"
    #cv2.imwrite(background_01, background_pic)
    #cv2.imwrite(slider01, slider_pic)
    #slider_pic = cv2.imread(slider01)
    slider_pic = cv2.cvtColor(slider_pic, cv2.COLOR_BGR2GRAY)
    slider_pic = abs(255 - slider_pic)
    slider_pic = cv2.GaussianBlur(slider_pic, (5, 5), 1)#图像处理减噪
    slider_pic = cv2.Canny(slider_pic, 300, 500)
    # cv2.imwrite(slider01, slider_pic)
    # slider_pic = cv2.imread(slider01)

    background_pic = cv2.imread(background_01)
    background_pic = cv2.cvtColor(background_pic, cv2.COLOR_BGR2GRAY)
    background_pic = abs(255 - background_pic)
    background_pic = cv2.GaussianBlur(background_pic, (3, 3), 1)#图像处理减噪
    background_pic = cv2.Canny(background_pic, 300, 400)
    cv2.imwrite(background_01, background_pic)
    background_pic = cv2.imread(background_01)      
    result = cv2.matchTemplate(slider_pic, background_pic, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)  
    cv2.rectangle(imgContour, max_loc, (max_loc[0] + 60, max_loc[1] + 60), (0, 0, 255), 2)
    top, left = np.unravel_index(result.argmax(), result.shape)
    print("当前滑块的缺口位置：", (left, top, left + width, top + height))
    left = left/ (width / 360)
    return left


def main():
    loginweb()

get_distance()
