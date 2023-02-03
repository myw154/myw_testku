# ---*--- utf-8 ---*---
# date: 2023-02-03
# author: meng
class SortMethod(object):

    def bubbleSort(self, arr):
        """
        冒泡排序，冒泡排序（Bubble Sort）也是一种简单直观的排序算法。它重复地走访过要排序的数列，一次比较两个元素，如果他们的顺序错误就把他们交换过来。走访数列的工作是重复地进行直到没有再需要交换，也就是说该数列已经排序完成。这个算法的名字由来是因为越小的元素会经由交换慢慢“浮”到数列的顶端。
        算法步骤:
            1.比较相邻的元素。如果第一个比第二个大，就交换他们两个。
            2.对每一对相邻元素作同样的工作，从开始第一对到结尾的最后一对。这步做完后，最后的元素会是最大的数。
            3.针对所有的元素重复以上的步骤，除了最后一个。
            4.持续每次对越来越少的元素重复上面的步骤，直到没有任何一对数字需要比较。
        """
        for i in range(1, len(arr)):
            for j in range(0, len(arr)-i):
                if arr[j] > arr[j+1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr

    def selectionSort(self, arr):
        """
        选择排序是一种简单直观的排序算法，无论什么数据进去都是 O(n²) 的时间复杂度。所以用到它的时候，数据规模越小越好。唯一的好处可能就是不占用额外的内存空间了吧。
        算法步骤:
            1.首先在未排序序列中找到最小（大）元素，存放到排序序列的起始位置
            2.再从剩余未排序元素中继续寻找最小（大）元素，然后放到已排序序列的末尾。
            3.重复第二步，直到所有元素均排序完毕。
        """
        for i in range(len(arr) - 1):
            # 记录最小数的索引
            minIndex = i
            for j in range(i + 1, len(arr)):
                if arr[j] < arr[minIndex]:
                    minIndex = j
            # i 不是最小数时，将 i 和最小数进行交换
            if i != minIndex:
                arr[i], arr[minIndex] = arr[minIndex], arr[i]
        return arr

    def insertionSort(arr):
        """
        插入排序的代码实现虽然没有冒泡排序和选择排序那么简单粗暴，但它的原理应该是最容易理解的了，因为只要打过扑克牌的人都应该能够秒懂。插入排序是一种最简单直观的排序算法，它的工作原理是通过构建有序序列，对于未排序数据，在已排序序列中从后向前扫描，找到相应位置并插入。
        插入排序和冒泡排序一样，也有一种优化算法，叫做拆半插入。
        算法步骤:
            1.将第一待排序序列第一个元素看做一个有序序列，把第二个元素到最后一个元素当成是未排序序列。
            2.从头到尾依次扫描未排序序列，将扫描到的每个元素插入有序序列的适当位置。（如果待插入的元素与有序序列中的某个元素相等，则将待插入元素插入到相等元素的后面。）
        """
        for i in range(len(arr)):
            preIndex = i-1
            current = arr[i]
            while preIndex >= 0 and arr[preIndex] > current:
                arr[preIndex+1] = arr[preIndex]
                preIndex-=1
            arr[preIndex+1] = current
        return arr

    def shellSort(self, arr):
        """
        希尔排序，也称递减增量排序算法，是插入排序的一种更高效的改进版本。但希尔排序是非稳定排序算法。
        希尔排序是基于插入排序的以下两点性质而提出改进方法的：
        插入排序在对几乎已经排好序的数据操作时，效率高，即可以达到线性排序的效率；
        但插入排序一般来说是低效的，因为插入排序每次只能将数据移动一位；
        希尔排序的基本思想是：先将整个待排序的记录序列分割成为若干子序列分别进行直接插入排序，待整个序列中的记录“基本有序”时，再对全体记录进行依次直接插入排序。
        算法步骤:
            1.选择一个增量序列 t1，t2，……，tk，其中 ti > tj, tk = 1；
            2.按增量序列个数 k，对序列进行 k 趟排序；
            3.每趟排序，根据对应的增量 ti，将待排序列分割成若干长度为 m 的子序列，分别对各子表进行直接插入排序。仅增量因子为 1 时，整个序列作为一个表来处理，表长度即为整个序列的长度。
        """
        import math
        gap=1
        while(gap < len(arr)/3):
            gap = gap*3+1
        while gap > 0:
            for i in range(gap,len(arr)):
                temp = arr[i]
                j = i-gap
                while j >=0 and arr[j] > temp:
                    arr[j+gap]=arr[j]
                    j-=gap
                arr[j+gap] = temp
            gap = math.floor(gap/3)
        return arr

    def mergeSort(self, arr):
        """
        归并排序（Merge sort）是建立在归并操作上的一种有效的排序算法。该算法是采用分治法（Divide and Conquer）的一个非常典型的应用。
        作为一种典型的分而治之思想的算法应用，归并排序的实现由两种方法：
        自上而下的递归（所有递归的方法都可以用迭代重写，所以就有了第 2 种方法）；
        自下而上的迭代；
        和选择排序一样，归并排序的性能不受输入数据的影响，但表现比选择排序好的多，因为始终都是 O(nlogn) 的时间复杂度。代价是需要额外的内存空间。

        算法步骤:
            1.申请空间，使其大小为两个已经排序序列之和，该空间用来存放合并后的序列；
            2.设定两个指针，最初位置分别为两个已经排序序列的起始位置；
            3.比较两个指针所指向的元素，选择相对小的元素放入到合并空间，并移动指针到下一位置；
            4.重复步骤 3 直到某一指针达到序列尾；
            5.将另一序列剩下的所有元素直接复制到合并序列尾。
        """
        import math
        if(len(arr)<2):
            return arr
        middle = math.floor(len(arr)/2)
        left, right = arr[0:middle], arr[middle:]
        return self.merge(self.mergeSort(left), self.mergeSort(right))

    def merge(self, left,right):
        result = []
        while left and right:
            if left[0] <= right[0]:
                result.append(left.pop(0));
            else:
                result.append(right.pop(0));
        while left:
            result.append(left.pop(0));
        while right:
            result.append(right.pop(0));
        return result

    def quick_sort(self, alist,start,end):
        """
        快速排序是由东尼·霍尔所发展的一种排序算法。在平均状况下，排序 n 个项目要 Ο(nlogn) 次比较。在最坏状况下则需要 Ο(n2) 次比较，但这种状况并不常见。事实上，快速排序通常明显比其他 Ο(nlogn) 算法更快，因为它的内部循环（inner loop）可以在大部分的架构上很有效率地被实现出来。
        快速排序使用分治法（Divide and conquer）策略来把一个串行（list）分为两个子串行（sub-lists）。
        快速排序又是一种分而治之思想在排序算法上的典型应用。本质上来看，快速排序应该算是在冒泡排序基础上的递归分治法。
        快速排序的名字起的是简单粗暴，因为一听到这个名字你就知道它存在的意义，就是快，而且效率高！它是处理大数据最快的排序算法之一了。虽然 Worst Case 的时间复杂度达到了 O(n²)，但是人家就是优秀，在大多数情况下都比平均时间复杂度为 O(n logn) 的排序算法表现要更好，可是这是为什么呢，我也不知道。好在我的强迫症又犯了，查了 N 多资料终于在《算法艺术与信息学竞赛》上找到了满意的答案：
        快速排序的最坏运行情况是 O(n²)，比如说顺序数列的快排。但它的平摊期望时间是 O(nlogn)，且 O(nlogn) 记号中隐含的常数因子很小，比复杂度稳定等于 O(nlogn) 的归并排序要小很多。所以，对绝大多数顺序性较弱的随机数列而言，快速排序总是优于归并排序。

        算法步骤:
            1.从数列中挑出一个元素，称为 “基准”（pivot）;
            2.重新排序数列，所有元素比基准值小的摆放在基准前面，所有元素比基准值大的摆在基准的后面（相同的数可以到任一边）。在这个分区退出之后，该基准就处于数列的中间位置。这个称为分区（partition）操作；
            3.递归地（recursive）把小于基准值元素的子数列和大于基准值元素的子数列排序；
递归的最底部情形，是数列的大小是零或一，也就是永远都已经被排序好了。虽然一直递归下去，但是这个算法总会退出，因为在每次的迭代（iteration）中，它至少会把一个元素摆到它最后的位置去。
        """
        if start >= end:
            return
        mid = alist[start]
        low=start
        hight=end
        while low<hight:
            while low<hight and alist[hight]>=mid:
                hight-=1
            alist[low]=alist[hight]
            while low<hight and alist[low]<mid:
                low += 1
            alist[hight] = alist[low]
        alist[low]=mid
        quick_sort(alist, start, low-1)
        quick_sort(alist, low+1, end)
        return alist




















