import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
lowThreshold = 0
maxThreshold = 100
max_lowThreshold = 500
max_maxThreshold = 1000
# 最小阈值范围 0 ~ 500
# 最大阈值范围 100 ~ 1000

def canny_low_threshold(intial):
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    canny = cv2.Canny(blur, intial, maxThreshold)
    cv2.imshow('canny', canny)
    # cv2.waitKey(200)


def canny_max_threshold(intial):
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    canny = cv2.Canny(blur, lowThreshold, intial)
    cv2.imshow('canny', canny)
    # cv2.waitKey()


# 参数0以灰度方式读取
img = cv2.imread(BASE_DIR + '/img.png', 0)
# cv2.imshow('11', img)
# cv2.waitKey()

# img.imshow()
# import pdb
# pdb.set_trace()
cv2.namedWindow('canny', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.createTrackbar('Min threshold', 'canny', lowThreshold, max_lowThreshold, canny_low_threshold)
cv2.createTrackbar('Max threshold', 'canny', maxThreshold, max_maxThreshold, canny_max_threshold)
canny_low_threshold(0)

# esc键退出
if cv2.waitKey(0) == 27:
    cv2.destroyAllWindows()
