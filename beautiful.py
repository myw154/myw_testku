# coding: utf-8

import os
import sys
import json
import subprocess
from random import randint


def remind():
    if len(sys.argv) < 3:
        print('参数错误')
        print('示例如下')
        print('\tpython %s input_file out_file' % sys.argv[0])
        sys.exit(-1)


def main():
    remind()
    file_path = sys.argv[1]
    f_c = open(sys.argv[2], 'w')
    model = input('请问你是想美化输出，还是抽样 y/n?\n')
    if model == 'n':
        check_num = input('请输入抽查的数量,默认：300\n')
    else:
        check_num = 300
    data_type = input('数据类型，j:json, s:str, 输入: j 或 s\n')
    if model != 'n':
        for line in open(file_path):
            json_data = json.loads(line.strip())
            print(json.dumps(json_data, ensure_ascii=False, indent=4),file=f_c)
    else:
        random_num_l = []
        a = subprocess.getstatusoutput('wc -l %s' % file_path)[1]
        len_file = int(a.split()[0])
        for i in range(0, int(check_num)):
            num = randint(0, len_file-1)
            random_num_l.append(num)

        for index, line in enumerate(open(file_path)):
            if index in random_num_l:
                if data_type == 's':
                    print(line.strip(), file=f_c)
                elif data_type == 'j':
                    json_data = json.loads(line.strip())
                    print(json.dumps(json_data, ensure_ascii=False, indent=2), file=f_c)
    f_c.close()


if __name__ == '__main__':
    main()
