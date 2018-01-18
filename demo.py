import time
import queue
import requests
from threading import Thread


# 多线程下载
class DownloadTask(Thread):

    def __init__(self, file_info, running_task):
        super().__init__(name=file_info['file_name'])

        self.__file_info = file_info
        self.__downloaded_size = 0
        self.__download_progress = 0

        self.__running_task = running_task

    def __str__(self):
        return self.__file_name

    # 在 run 中开始下载
    def run(self):
        try:
            self.start_download()
            # 执行下载完成后的动作
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
        with open(self.__file_info['file_name'], 'ab+') as f:
            for i in res.iter_content(chunk_size=1024):
                if not self.__file_info['file_size'] == 0:
                    # 更新进度
                    self.__downloaded_size += 1024
                    self.__download_progress = int(
                        self.__downloaded_size /
                        self.__file_info['file_size'] * 100)
                else:
                    self.__downloaded_size += 1024
                    self.__download_progress = 0

                f.write(i)

    # 获取文件大小
    def get_download_progress(self):
        self.__file_info['download_progress'] = self.__download_progress
        return self.__file_info


# 下载任务管理类
class DownloadPool(Thread):

    def __init__(self, running_max_size=3, waiting_max_size=10):
        super().__init__(name="download_pool")
        self.running_max_size = running_max_size
        self.waiting_max_size = waiting_max_size

        self.__pool_running = True
        self.__running_task = []
        self.__waiting_queue = queue.Queue(waiting_max_size)

    def run(self):
        # 循环监控正在运行的线程, 当有任务完成时, 开始队列中的任务
        while self.__pool_running:
            if len(self.__running_task) < 3 and \
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
        return [task.get_download_progress() for task in self.__running_task]


# 程序主入口
if __name__ == '__main__':
    BASE_URL = 'http://120.78.90.156/api/v1'

    file_url = 'http://sw.bos.baidu.com/sw-search-sp/software/7f64d1528e001/Sublime_Text_3.3143_Setup.exe'
    game_url = 'http://dlsw.baidu.com/sw-search-sp/soft/85/21019/HeroAcademy_1.0.0.1039.2313078873.exe'
    video_url = 'http://dl161.80s.im:920/1712/追龙/追龙.mp4'

    res = requests.get(file_url)
    file_size = int(res.headers['Content-Length'])

    # 实例化下载池
    download_pool = DownloadPool()
    download_pool.start()

    print('Build pool')

    # 创建十个下载任务
    for i in range(10):
        file_info = {
            'file_name': '%d.exe' % i,
            'file_size': file_size,
            'download_link': file_url,
        }

        # 添加任务到下载池, 添加任务只需要提供下载的信息即可
        download_pool.put(file_info)
        print('Add a download task')

    progress = download_pool.get_all_task_progress()
    while len(progress) != 0:
        for i in progress:
            print(i['file_name'], i['download_progress'])
        time.sleep(5)
        progress = download_pool.get_all_task_progress()
