import getopt
import sys

def usage():
    print ("=======")
    print ("Usage:")
    print ("python test_getopt.py -I:127.0.0.1 -p:8888 66 88 or python test_getopt.py --ip=127.0.0.1 --port=8888 66 88")
    print ("=======")

def main():
    """getopt 模块的用法"""
    options, args = getopt.getopt(sys.argv[1:], 'h:p:i:', ['help', 'port=', 'ip='])
    for name, value in options:
        if name in ('-h', '--help'):
            usage()
        if name in ('-p', '--port'):
            print ('value: {0}'.format(value))
        if name in ('-i', '--ip'):
            print ('value: {0}'.format(value))
    for name in args:
        # name 的值就是 上边参数实例里边的66和88
        print ("name: {0}".format(name))

def main_test():
    options, args = getopt.getopt(sys.argv[1:], 'name:', ['name=', 'query='])
    import pdb
    pdb.set_trace()
    print(options)
    print(args)

if __name__ == "__main__":
    main_test()
    # main()

