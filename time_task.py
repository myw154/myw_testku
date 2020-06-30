import schedule
import time
import os
import psutil
from datetime import datetime


def test2():
    print("I'm working... in job2")
    print(datetime.now())
    time.sleep(5)
    print("I'havend done")

def main():
    schedule.every().day.at("18:39").do(test2)
    i = 1
    while True:
        # 启动服务
        schedule.run_pending()
        time.sleep(1)
        print('我休息了 %s s' % i)
        i += 1
main()

