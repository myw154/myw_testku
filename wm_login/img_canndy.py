import cv2
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def matchImg(imgPath1,imgPath2):
    # import pdb
    # pdb.set_trace()
    # 原始图像，用于展示
    sou_img1 = cv2.imread(imgPath1)
    sou_img2 = cv2.imread(imgPath2)

    # 原始图像，灰度
    # 最小阈值100,最大阈值500
    img1 = cv2.imread(imgPath1, 0)
    blur1 = cv2.GaussianBlur(img1, (3, 3), 0)
    canny1 = cv2.Canny(blur1, 100, 200)
    cv2.imwrite(BASE_DIR + '/temp1.png', canny1)
    # 标签图片
    img2 = cv2.imread(imgPath2, 0)
    blur2 = cv2.GaussianBlur(img2, (3, 3), 0) # 高斯模糊
    canny2 = cv2.Canny(blur2, 100, 500) # 边缘算法
    cv2.imwrite(BASE_DIR + '/temp2.png', canny2)

    # 读取处理完成图片
    target = cv2.imread(BASE_DIR + '/temp1.png')
    template = cv2.imread(BASE_DIR + '/temp2.png')

    # 匹配拼图
    """
    cv::InputArray image, // 用于搜索的输入图像, 8U 或 32F, 大小 W-H
		cv::InputArray templ, // 用于匹配的模板，和image类型相同， 大小 w-h
		cv::OutputArray result, // 匹配结果图像, 类型 32F, 大小 (W-w+1)-(H-h+1)
		int method
    cv::TM_CCORR_NORMED：归一化的相关性匹配方法，与相关性匹配方法类似，最佳匹配位置也是在值最大处
    """
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    # 归一化
    cv2.normalize(result, result, 0, 1, cv2.NORM_MINMAX, -1)
    # 提取result中点最佳位置
    _, _, _, max_loc = cv2.minMaxLoc(result)
    print(max_loc)
    return max_loc


if __name__ == "__main__":
    matchImg(BASE_DIR + '/img.png', BASE_DIR + '/img_2.png')
