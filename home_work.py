def split_file(big_file_path):
    with open(big_file_path, 'r', encoding='utf-8') as f:
        info_list = f.readlines(1024*1024*500)
        i = 0
        while info_list:
            file_name = big_file_path.split('/')[-1].split('.')[0]

            # 需要对 info_list进行排序之后写入文件
            info_sort_list = mgerge_sort(info_list)
            new_file_path = big_file_path.replace(big_file_path.split(r'/')[-1], '')+file_name+r'/'+file_name+r'_new'+str(i)+r'.txt'
            with open(new_file_path, 'w', encoding='utf-8') as new_f:
                new_f.write(str(info_sort_list))
            i += 1
            info_list = f.readlines(1024*1024*500)
split_file()
# 排序算法
def merge_sort(alist):
    if len(alist) <= 1:
        return alist
    num = len(alist)//2
    left_list = merge_sort(alist[:num])
    right_list = merge_sort(alist[num:])
    return merge(left_list, right_list)


def merge(left_list, right_list):
    l, r = 0, 0
    result = []
    while l < len(left_list) and r < len(right_list):
        if left_list[l] < right_list[r]:
            result.append(left_list[l])
            l += 1
        else:
            result.append(right_list[r])
            r += 1
    result += left_list[l:]
    result += right_list[r:]
    return result
info_list = [10, 20, 2, 45, 33, 33, 24, 55, 24]
merge_sort(info_list)
print(merge_sort(info_list))

