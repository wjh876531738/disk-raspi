import requests
import json


def update():
    res = requests.get('http://120.78.90.156/api/v1/file_info/51')
    if res.ok:
        print(json.dumps(res.json(), indent=2))

        data = res.json()
        data['save_path'] = 'asdsd'
        data['file_type'] = 'exe'

        url = 'http://120.78.90.156/api/v1/file_info/51'
        new_res = requests.put(url, data=data)

        print(new_res.status_code)
        print(json.dumps(new_res.json(), indent=2))


def download_file():
    url = 'http://dl161.80s.im:920/1712/追龙/追龙.mp4'
    res = requests.get(url, stream=True)

    file_size = int(res.headers['Content-Length'])
    download_progress = 0
    downloaded_size = 0
    with open('./test.mp4', 'ab+') as f:
        for i in res.iter_content(chunk_size=1024):
            downloaded_size += 1024
            download_progress = downloaded_size / file_size * 100
            print('%d %s' % (download_progress, '%'))
            f.write(i)


def test():
    name = [1, 2]
    name[1]()


if __name__ == '__main__':
    # update()
    # download_file()

    print("Hello world")
