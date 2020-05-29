# coding:utf-8

import sys
import os
import hashlib


class FileRemoveDup(object):

    def __init__(self, node_size=1, num=0):
        self.num = num  # 临时文件递增序号
        self.node_size = node_size  # 每次读取字符数，防止内存占用过高

    def sorted_file_rm_duplicate(self, file1_path, file2_path, file3_path):
        '''有序文件去重'''
        file1_fp1, file1_fp2 = open(file1_path), open(file1_path)
        file2_fp1, file2_fp2 = open(file2_path), open(file2_path)

        fp1_md5 = self.fp_md5(file1_fp1)
        fp2_md5 = self.fp_md5(file2_fp1)

        fp3 = open(file3_path, 'w')

        while fp1_md5 and fp2_md5:
            if fp1_md5 > fp2_md5:
                fp2_md5 = self.fp_md5(file2_fp1)
                file2_fp2.readline()
            elif fp1_md5 == fp2_md5:
                file1_fp2.readline()
                fp1_md5 = self.fp_md5(file1_fp1)
            else:
                fp3.write(file1_fp2.readline())
                fp1_md5 = self.fp_md5(file1_fp1)
        # 如果fp1有剩余
        if fp1_md5:
            self.for_file_write(fp3, file1_fp2)

        file_list = [file1_fp1, file1_fp2, file2_fp1, file2_fp2, fp3]
        self.for_file_close(file_list)

    def file_sort(self, file_path, new_file_name):
        '''文件内部排序'''
        '''
        file_path     :待排序文件路径
        new_file_name :排序后文件名
        node_size     :文件分割大小，单位字符个数
        '''
        res_file_list = self.file_split(file_path)
        if not res_file_list:
            raise Exception('分割文件失败')
        # 块数据排序整合到排序后文件
        new_file = self._merge_file_sort(res_file_list)
        os.system('mv %s %s' % (new_file, new_file_name))
        return new_file_name

    def file_split(self, file_path):
        '''
        file_path: 文件路径
        node_size: 文件分割大小，单位字符个数
        '''
        res_file_list = []
        with open(file_path, 'r') as f:
            while True:
                # 读出指定字符数，最后一个字符为换行符会读出下一行
                file_list = f.readlines(self.node_size)
                if not file_list:
                    break
                # 获取归并排序后数据
                file_merged = self.merge_sort(file_list)
                tem_file_name = '%s_%s' % (file_path, len(res_file_list))
                # 排序后的数据写到临时文件
                with open(tem_file_name, 'w') as fp:
                    self.for_file_write(fp, file_merged)
                # 把临时文件名加到文件列表
                res_file_list.append(tem_file_name)

        return res_file_list

    def _merge_file_sort(self, array):
        '''文件名列表归并排序'''
        if len(array) <= 1:
            return array[0]
        mid = len(array) // 2
        left = self._merge_file_sort(array[:mid])   # 归并左列表
        right = self._merge_file_sort(array[mid:])  # 归并右列表
        return self.merge_file(left, right)

    def get_file_name(self):
        '''生成临时文件名'''
        file_name = 'tem_{}'.format(self.num)
        self.num += 1
        return file_name

    def for_file_write(self, fp, filename):
        for line in filename:
            fp.write(line)

    def for_file_close(self, file_list):
        for file in file_list:
            file.close()

    def fp_md5(self, fp):
        string = fp.readline()
        if string:
            m = hashlib.md5()
            m.update(string.encode())
            md5 = m.hexdigest()
            del string
            return md5

    def merge_file(self, file_1, file_2):
        '''文件归并排序'''
        file1_fp1, file1_fp2 = open(file_1), open(file_1)
        file2_fp1, file2_fp2 = open(file_2), open(file_2)

        fp1_md5 = self.fp_md5(file1_fp1)
        fp2_md5 = self.fp_md5(file2_fp1)

        file_3 = self.get_file_name()
        fp3 = open(file_3, 'w')

        while fp1_md5 and fp2_md5:
            if fp1_md5 > fp2_md5:
                fp3.write(file2_fp2.readline())
                fp2_md5 = self.fp_md5(file2_fp1)
            else:
                fp3.write(file1_fp2.readline())
                fp1_md5 = self.fp_md5(file1_fp1)
        # 如果fp1有剩余
        if fp1_md5:
            self.for_file_write(fp3, file1_fp2)
        else:
            self.for_file_write(fp3, file2_fp2)

        file_list = [file1_fp1, file1_fp2, file2_fp1, file2_fp2, fp3]
        self.for_file_close(file_list)
        # 移除临时文件
        os.remove(file_1)
        os.remove(file_2)
        return file_3

    def merge_sort(self, array):
        '''列表归并排序'''
        '''
        array: 列表类型参数
        '''
        if isinstance(array, list):
            if len(array) <= 1:  # 如果是一个元素或者空元素
                return array
            mid = len(array) // 2  # 取中间位置xx
            left = self.merge_sort(array[:mid])  # 归并左列表
            right = self.merge_sort(array[mid:])  # 归并右列表
        else:
            raise Exception('{} is not list'.format(array))
        return self.merge(left, right)  # 返回

    def merge(self, left, right):
        ''' 归并排序逻辑'''
        merged = []
        i, j = 0, 0
        left_len, right_len = len(left), len(right)

        while i < left_len and j < right_len:
            # 先追加较小的元素
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
                # 追加剩余元素
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    def run(self, file1, file2, file3):
        # 将两个大文件进行归并排序
        file1_sort = self.file_sort(file1, file1 + '_sort')
        file2_sort = self.file_sort(file2, file2 + '_sort')

        # 对两个排序好的文件进行去重
        self.sorted_file_rm_duplicate(file1_sort, file2_sort, file3)


def _remind():
    if len(sys.argv) < 4:
        print('用法错误')
        print('示例如下：')
        print('python {} file_path01 file_path02 file_path03'.format(
            sys.argv[0]))
        print('''
              file_path01为将要去重的文件
              file_path02为对比文件
              file_path03为去重后的新文件
              ''')
        sys.exit(-1)


def main():
    try:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
        file3 = sys.argv[3]
        file_remove_dup = FileRemoveDup()
        file_remove_dup.run(file1, file2, file3)
    except:
        _remind()


if __name__ == '__main__':
    main()
