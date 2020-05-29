import fitz
import os
import sys


def get_pre_pdf(pdf_path,  out_path):
    doc = fitz.open(pdf_path)
    pdf_name = os.path.basename(pdf_path).replace('.pdf', '')
    print(pdf_name)
    #if not os.path.exists(os.path.join(out_path, pdf_name)):
    #    os.makedirs(os.path.join(out_path, pdf_name))
    img_path = os.path.join(out_path, pdf_name+'_{}.jpg')
    totaling = doc.pageCount
    print(totaling)
    for pg in range(0, totaling):
        page = doc[pg]
        trans = fitz.Matrix(100 / 100.0, 100 / 100.0).preRotate(0)
        pm = page.getPixmap(matrix=trans, alpha=False)
        pm.writePNG(img_path.format(pg))

# pdf_dir是pdf绝对路径，out_dir 为解析图片的存储路径
def get_all_pdf():
    if len(sys.argv) < 3:
        print('parameters error')
        sys.exit(-1)
        # pdf 文件目录
    pdf_dir = sys.argv[1]
    out_dir = sys.argv[2]
    i= 1
    for dir_path, sub_dirs, sub_files in os.walk(pdf_dir):
        print(len(sub_files))
        for sub_file in sub_files:
            # 列报表中存在一个'.DS_Store'的隐藏文件
            if sub_file.startswith('.') or (not sub_file.endswith('.pdf')):
                continue
            # 拼接文件的路径
            print('正在解析第{}个pdf文件'.format(i))
            pdf_file = os.path.join(dir_path, sub_file)
            try:
                get_pre_pdf(pdf_file, out_dir)
            except Exception:
                with open(out_dir+'/../error_name.txt', 'a', encoding='utf-8') as f:
                    f.write(pdf_file+'\n')
            i += 1

def analys_error():
    out_dir = sys.argv[1]
    with open(out_dir+'/../error_name.txt', 'r', encoding='utf-8') as f:
        file_path_list = f.readlines()
        for file_path in file_path_list:
            get_pre_pdf(file_path.replace('\n', ''), out_dir)


def main():
    get_all_pdf()
    #analys_error()

if __name__ == '__main__':
    main()
