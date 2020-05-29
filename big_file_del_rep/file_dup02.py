import sys
import os

NUM = 0


'''没有封装为类版本'''
def sorted_file_rm_duplicate(file1_path, file2_path, file3_path):
    fp1, f1_line = file_readline(file1_path)
    fp2, f2_line = file_readline(file2_path)
    fp3 = open(file3_path, 'w')

    while f1_line and f2_line:
        if f1_line > f2_line:
            f2_line = fp2.readline()
        elif f1_line == f2_line:
            f1_line = fp1.readline()
        else:
            fp3.write(f1_line)
            f1_line = fp1.readline()
    if f1_line:
        fp3.write(f1_line)
        for line in fp1:
            fp3.write(line)
    for f in [fp1, fp2, fp3]:
        f.close()


# 文件内部排序
def file_sort(file_path, new_file_name, node_size=1000):
    '''
    file_path     :待排序文件路径
    new_file_name :排序后文件名
    node_size     :文件分割大小，单位字符个数
    '''
    res_file_list = file_split(file_path, node_size)
    if not res_file_list:
        raise Exception('分割文件失败')
    else:
        # 块数据排序整合到排序后文件
        new_file = merge_file_sort(res_file_list)
        os.system('mv %s %s' % (new_file, new_file_name))
    return new_file_name


def file_split(file_path, node_size=1000):
    '''
    file_path: 文件路径
    node_size: 文件分割大小，单位字符个数
    '''
    res_file_list = []
    with open(file_path, 'r') as f:
        while True:
            # 读出指定字符数，最后一个字符为换行符会读出下一行
            file_list = f.readlines(node_size)
            if not file_list:
                break
            # 获取归并排序后数据
            file_merged = merge_sort(file_list)
            tem_file_name = '%s_%s' % (file_path, len(res_file_list))
            # 排序后的数据写到临时文件
            with open(tem_file_name, 'w') as fp:
                for line in file_merged:
                    fp.write(line)
                # 把临时文件名加到文件列表
                res_file_list.append(tem_file_name)
    return res_file_list


# 文件名列表归并排序
def merge_file_sort(array):
    if len(array) <= 1:
        return array[0]
    mid = len(array) // 2
    left = merge_file_sort(array[:mid])   # 归并左列表
    right = merge_file_sort(array[mid:])  # 归并右列表
    return merge_file(left, right)


def file_readline(file_path):
    '''
    file_path: 文件路径
    注：调用该函数注意 fp.close()
    '''
    fp = open(file_path)
    fp_line = fp.readline()
    return fp, fp_line


def get_file_name():
    global NUM
    file_name = 'tem_{}'.format(NUM)
    NUM += 1
    return file_name


# 文件排序
def merge_file(file_1, file_2):

    fp1, fp1_line = file_readline(file_1)
    fp2, fp2_line = file_readline(file_2)

    file_3 = get_file_name()
    fp3 = open(file_3, 'w')
    while fp1_line and fp2_line:
        if fp1_line > fp2_line:
            fp3.write(fp2_line)
            fp2_line = fp2.readline()
        else:
            fp3.write(fp1_line)
            fp1_line = fp1.readline()
    # 如果fp1有剩余
    if fp1_line:
        fp3.write(fp1_line)
        for line in fp1:
            fp3.write(line)
    else:
        fp3.write(fp2_line)
        for line in fp2:
            fp3.write(line)
    for fp in [fp1, fp2, fp3]:
        fp.close()
    # 移除临时文件
    os.remove(file_1)
    os.remove(file_2)
    return file_3


# 列表归并排序
def merge_sort(array):
    '''
    array: 列表参数
    '''
    if len(array) <= 1:  # 如果是一个元素或者空元素
        return array
    mid = len(array) // 2  # 取中间位置
    left = merge_sort(array[:mid])  # 归并左列表
    right = merge_sort(array[mid:])  # 归并右列表
    return merge(left, right)  # 返回


# 归并排序逻辑
def merge(left, right):
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


def remind():
    if len(sys.argv) < 4:
        print('用法错误')
        print('示例如下：')
        print('python {} file01_path file02_path file03_path'.format(
            sys.argv[0]))
        print('''
              file01_path为将要去重的文件
              file02_path为对比文件
              file03_path为去重后的新文件
              ''')
        sys.exit(-1)


def main():
    remind()
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    file3 = sys.argv[3]

    # 将两个大文件进行归并排序
    file1_sort = file_sort(file1, file1 + '_sort')
    file2_sort = file_sort(file2, file2 + '_sort')

    # 对两个排序好的文件进行去重
    sorted_file_rm_duplicate(file1_sort, file2_sort, file3)


if __name__ == '__main__':
    main()
