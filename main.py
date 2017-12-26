import os                            # 系统包, 创建文件夹
import json                          # 解析 MQTT 内容
import requests                      # 发送网络请求, 下载文件
import paho.mqtt.client as mqtt      # MQTT包

from downloader import DownloadPool  # 下载池, 用于处理下载请求
import utils                         # 工具包


# 下载文件
def download_file(client, file_info):
    if os.path.exists(os.path.join(BASE_DIR,
                                   file_info['file_path'],
                                   file_info['file_name'])):
        print(os.path.join(BASE_DIR,
                           file_info['file_path'],
                           file_info['file_name']))
        recall_msg(client, 0, '错误! 文件名重复')
    else:
        # 避免字符串包含空格
        file_info['download_link'] = file_info['download_link'].strip()
        file_info['file_name'] = os.path.basename(file_info['download_link'])

        # 根据文件名获取文件类型
        file_info['file_type'] = os.path.splitext(
            file_info['file_name'])[1][1:]

        # 获取下载文件的文件大小
        res = requests.get(file_info['download_link'], stream=True)
        if 'Content-Length' in res.headers:
            file_size = res.headers['Content-Length']
        else:
            file_size = 0

        file_info['file_size'] = file_size
        file_info['download_status'] = 0

        # 保存到数据库
        res = requests.post(BASE_URL+'/file_list', data=file_info)
        print(res.json())
        if res.ok and res.status_code == 201:
            recall_msg(client, 0, '开始下载')

            file_info = res.json()
            file_info['save_path'] = os.path.join(
                BASE_DIR,
                file_info['file_path'],
                file_info['file_name'],
            )

            # 把下载任务的信息放入到下载池中
            download_pool.put(file_info)
        else:
            recall_msg(client, 0, '下载失败, 下载链接无效')


# 创建目录
def mkdir(client, file_info):
    print(os.path.join(BASE_DIR, file_info['file_path']))
    if os.path.exists(os.path.join(BASE_DIR, file_info['file_path'])):
        recall_msg(client, 0, '目录已存在')
    else:
        res = requests.post(BASE_URL+'/file_list', data=file_info)
        if res.ok and res.status_code == 201:
            os.mkdir(os.path.join(BASE_DIR, file_info['file_path']))
            recall_msg(client, 0, '创建成功')
        else:
            recall_msg(client, 0, '创建失败')


# 连接 mqtt服务
def on_connect(client, userdata, flags, rc):
    client.subscribe('disk')
    print('Connect success, subscribe the `disk` topic', end='\n\n')


# Mqtt 回调
# 读取发布内容, 根据网页发布内容的操作指示进行相应的操作
def on_message(client, userdata, msg):
    try:
        payload = eval(msg.payload)
        print(payload)

        if 'op' in payload:
            if payload['op'] == 'mkdir':
                mkdir(client, payload['data'])

            elif payload['op'] == 'download':
                download_file(client, payload['data'])

            elif payload['op'] == 'download_progress':
                recall_msg(client, 1, download_pool.get_all_task_progress())

            elif payload['op'] == 'get_raspi_ip':
                recall_msg(client, 2, LOCAL_IP_ADDRESS)

            elif payload['op'] == 'get_download_filename':
                download_link = payload['data']['download_link']
                filename = os.path.basename(download_link)

                recall_msg(client, 3, filename)

        else:
            recall_msg(client, 0, '错误! 数据当中没有`op`键')

    except Exception as e:
        print(e)
        recall_msg(client, 0, '错误! 请发送JSON格式的数据')


# 发布"操作结果"到 'disk/recall' 话题
def recall_msg(client, status, msg):
    send_payload = {}
    send_payload['status'] = status
    send_payload['msg'] = msg

    client.publish('disk/recall', json.dumps(send_payload))


# 程序入口
if __name__ == '__main__':
    HOST = '120.78.90.156'
    BASE_DIR = 'files'
    BASE_URL = 'http://120.78.90.156/api/v1'

    # 获取本机局域网IP
    LOCAL_IP_ADDRESS = utils.getip()

    # 定义接入服务器的 MQTT 平台的变量
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # 接入 MQTT 平台, 无限循环, 监听`网盘操作`话题的内容
        client.connect(HOST, 1883, 60)

        # 实例化下载线程池
        download_pool = DownloadPool()
        download_pool.start()

        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()
