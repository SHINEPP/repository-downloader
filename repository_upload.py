import requests
from requests.auth import HTTPBasicAuth


def upload():
    group_id = 'com.shine.test5'
    artifact_id = 'alpha'
    version = '1.0.1'
    upload_repository_url = 'https://maven.cherrysoft.cn/service/rest/v1/components?repository=maven-releases'
    username = 'develop'
    password = '1234567890'

    aar_file_path = '/Users/zhouzhenliang/Desktop/temp/maven/develop-gp-10.7.2.0.aar'
    pom_file_path = '/Users/zhouzhenliang/Desktop/temp/maven/develop-gp-10.7.2.0.pom'

    # 准备要上传的文件
    files = {
        'maven2.asset1': open(aar_file_path, 'rb'),
        'maven2.asset1.extension': (None, 'aar'),
        'maven2.asset2': open(pom_file_path, 'rb'),
        'maven2.asset2.extension': (None, 'pom'),
        'maven2.groupId': (None, group_id),
        'maven2.artifactId': (None, artifact_id),
        'maven2.version': (None, version),
    }

    # 通过 HTTP POST 上传 AAR 文件
    response = requests.post(upload_repository_url, files=files, auth=HTTPBasicAuth(username, password))

    if response.status_code == 201:
        print('AAR 文件上传成功！')
    else:
        print(f'上传失败: {response.status_code}, {response.text}')


if __name__ == '__main__':
    upload()
