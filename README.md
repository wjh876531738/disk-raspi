# Python 实现多线程下载 (Python3)

> 我们在爬虫的过程中往往需要下载大量文件. 虽然网上也有很多 Python 多线程下载文件的文章, 但是大多都不能达到自己的目的, 故此为了达到更好的效果我采用 threading, queue, requests 包实现了一套可定制化的多线程下载

## 包的作用
   - requests 实现文件下载的网络请求库
   - threading 实现多线程
   - queue 根据队列, 对下载任务使用队列管理

## 实现流程

### 导包

```
import requests
import queue
from threading import Thread
```

### 使用 requests 实现文件下载

```
# 建立与下载目标文件的链接 (这里给了个百度应用下载的 sublime 安装包下载, 大家可自行选择下载链接进行尝试)
download_link = 'http://sw.bos.baidu.com/sw-search-sp/software/7f64d1528e001/Sublime_Text_3.3143_Setup.exe'
res = requests.get(download_link, stream=True)

# 根据请求头获取目标文件的大小
file_size = res.headers['Content-Length']
print('文件大小为:', file_size)

# 遍历文件内容保存到本地
with open('sublime.exe', 'ab+') as f:
     for i in res.iter_content(chunk_size=1024):
         f.write(i)
```

### 使用 threading 的 Thread 实现多线程

我们先对之前实现的文件下载代码进行封装, 并实现获取下载进度功能

```
# 下载任务类
class DownloadTask():

    def __init__(self, file_info):
        self.__file_info = file_info

        # 初始化下载进度相关变量
        self.__download_size = 0
        self.__download_progress = 0

    # 开始下载
    def start_download(self):
        # 流式下载文件, 每次下载1024个字节
        res = requests.get(self.__file_info['download_link'], stream=True)

        # 更新文件大小信息
        self.__file_info['file_size'] = res.headers['Content-Length']

        with open(self.__file_info['file_name'], 'ab+') as f:
            for i in res.iter_content(chunk_size=1024):
                if not self.__file_info['file_size'] == 0:
                    # 更新下载进度
                    self.__downloaded_size += 1024
                    self.__download_progress = int(
                        self.__downloaded_size /
                        self.__file_info['file_size'] * 100)
                else:
                    self.__downloaded_size += 1024
                    self.__download_progress = 0

                f.write(i)


# 程序入口
if __name__ == '__main__':
    download_link = 'http://sw.bos.baidu.com/sw-search-sp/software/7f64d1528e001/Sublime_Text_3.3143_Setup.exe'

    file_info = {
        'file_name': 'sublime.exe',
        'file_size': 0,
        'download_link': download_link,
    }
    download_task = DownloadTask(file_info)
    download_task.start_download()
```

在对下载任务封装成类之后, 我们可以开始将下载任务类设计成多线程任务了
    1. 让 DownloadTask 类继承 Thread 类
    2. 在初始化中执行 Thread 父类的初始化
    3. 添加上 run 函数定义线程执行内容
    4. 在程序入口中创建下载任务线程并启动

```
# 下载任务类
class DownloadTask(Thread):

    def __init__(self, file_info):
        super().__init__(name=file_info['file_name'])
        self.__file_info = file_info

        # 初始化下载进度相关变量
        self.__downloaded_size = 0
        self.__download_progress = 0

    def run(self):
        try:
            print('开始下载')

            self.start_download()

            # 执行下载完成后的操作
            print('下载完成')
        except Exception as e:
            # 下载失败打印错误信息
            print(e)


    # 开始下载
    def start_download(self):
        # 流式下载文件, 每次下载1024个字节
        res = requests.get(self.__file_info['download_link'], stream=True)

        # 更新文件大小信息
        self.__file_info['file_size'] = int(res.headers['Content-Length'])

        with open(self.__file_info['file_name'], 'ab+') as f:
            for i in res.iter_content(chunk_size=1024):
                if not self.__file_info['file_size'] == 0:
                    # 更新下载进度
                    self.__downloaded_size += 1024
                    self.__download_progress = int(
                        self.__downloaded_size /
                        self.__file_info['file_size'] * 100)

                    print('下载进度:', self.__download_progress)
                else:
                    self.__downloaded_size += 1024
                    self.__download_progress = 0

                f.write(i)

# 程序入口
if __name__ == '__main__':
    download_link = 'http://sw.bos.baidu.com/sw-search-sp/software/7f64d1528e001/Sublime_Text_3.3143_Setup.exe'

    file_info = {
        'file_name': 'sublime.exe',
        'file_size': 0,
        'download_link': download_link,
    }
    download_task = DownloadTask(file_info)
    download_task.start()
```

### 在多线程的基础下引入队列保证下载任务的有序执行

添加一个下载任务管理类, 用于管理所有的下载任务, 限制最大同时下载数和最大等待下载队列. 所有的下载任务都必须通过下载任务管理类进行添加和管理

添加下载任务管理类, 并且使下载任务管理类作为线程启动. 在下载任务管理类中会包含两个变量: 正在下载的任务线程组成的列表 和 等待下载的队列

此时, 我们还需要在之前已经封装好的下载任务线程类补充补充

1. 初始化的参数添加上正在下载的任务线程组成的列表
2. 在下载完成后更新正在下载的任务线程组成的列表

最后, 补上代码, 也是整个项目的所有代码

```
# 下载任务类
class DownloadTask(Thread):

    def __init__(self, file_info, running_task):
        super().__init__(name=file_info['file_name'])
        self.__file_info = file_info

        # 初始化下载进度相关变量
        self.__downloaded_size = 0
        self.__download_progress = 0

        self.__running_task = running_task

    def run(self):
        try:
            print('开始下载', self.name)

            self.start_download()

            # 执行下载完成后的操作
            print('下载完成', self.name)
        except Exception as e:
            # 下载失败打印错误信息
            print(e)

        # 更新正在下载任务的列表
        for index, task in enumerate(self.__running_task):
            if task == self:
                self.__running_task.pop(index)
                break


    # 开始下载
    def start_download(self):
        # 流式下载文件, 每次下载1024个字节
        res = requests.get(self.__file_info['download_link'], stream=True)

        # 更新文件大小信息
        self.__file_info['file_size'] = int(res.headers['Content-Length'])

        with open(self.__file_info['file_name'], 'ab+') as f:
            for i in res.iter_content(chunk_size=1024):
                if not self.__file_info['file_size'] == 0:
                    # 更新下载进度
                    self.__downloaded_size += 1024
                    self.__download_progress = int(
                        self.__downloaded_size /
                        self.__file_info['file_size'] * 100)
                else:
                    self.__downloaded_size += 1024
                    self.__download_progress = 0

                f.write(i)

    def get_download_progress(self):
        return self.__download_progress


# 下载任务管理类
class DownloadPool(Thread):

    def __init__(self, running_max_size=3, waiting_max_size=10):
        super().__init__(name="download_pool")
        self.running_max_size = running_max_size
        self.waiting_max_size = waiting_max_size

        self.__pool_running = True  # 下载任务管理类线程的状态
        self.__running_task = []
        self.__waiting_queue = queue.Queue(waiting_max_size)

    def run(self):
        # 循环监控正在运行的线程, 当有任务完成时, 开始队列中的任务
        while self.__pool_running:
            if len(self.__running_task) < self.running_max_size and \
               not self.__waiting_queue.empty():
                download_task = self.__waiting_queue.get()
                self.__running_task.append(download_task)
                download_task.start()

    # 添加任务
    def put(self, file_info):
        # 如果正在下载的任务没超过限制, 则马上开始下载任务
        if len(self.__running_task) < self.running_max_size:
            download_task = DownloadTask(file_info, self.__running_task)
            self.__running_task.append(download_task)
            download_task.start()
            return True
        # 如果整下下载的任务超过了限制, 就先放入等待队列
        elif not self.__waiting_queue.full():
            download_task = DownloadTask(file_info, self.__running_task)
            self.__waiting_queue.put(download_task)
            return True
        else:
            return False

    def get_all_task_progress(self):
        return [[task.name, task.get_download_progress()] for task in self.__running_task]


# 程序入口
if __name__ == '__main__':
    download_link = 'http://sw.bos.baidu.com/sw-search-sp/software/7f64d1528e001/Sublime_Text_3.3143_Setup.exe'

    download_pool = DownloadPool()
    download_pool.start()

    for i in range(5):
        file_info = {
            'file_name': 'sublime%d.exe' % i,
            'file_size': 0,
            'download_link': download_link,
        }
        download_pool.put(file_info)

    download_progress = download_pool.get_all_task_progress()
    while len(download_progress) > 0:
        print(download_progress)
        download_progress = download_pool.get_all_task_progress()
```
