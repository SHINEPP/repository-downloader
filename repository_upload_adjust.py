import requests
from requests.auth import HTTPBasicAuth

from repository_upload import create_maven_pom


def upload_aar():
    repository_url = 'https://maven.cherrysoft.cn/service/rest/v1/components?repository=maven-releases'
    username = 'develop'
    password = 'qwert12345'

    group_id = 'com.adjust.sdk'
    artifact_id = 'adjust-android'
    version = '5.3.0-2025051301'
    packaging = 'aar'
    aar_file_path = '/Users/zhouzhenliang/Desktop/security_250513/adjust/build/adjust-android-5.3.0_20250513.aar'
    dependencies = []

    artifact_file = open(aar_file_path, 'rb')
    pom_bytes = create_maven_pom(group_id, artifact_id, version, packaging, dependencies)
    print(pom_bytes.decode())

    # 准备要上传的文件
    files = {
        'maven2.asset1': artifact_file,
        'maven2.asset1.extension': (None, 'aar'),
        'maven2.asset2': pom_bytes,
        'maven2.asset2.extension': (None, 'pom'),
        'maven2.groupId': (None, group_id),
        'maven2.artifactId': (None, artifact_id),
        'maven2.version': (None, version),
    }

    # 通过 HTTP POST 上传 AAR 文件
    response = requests.post(repository_url, files=files, auth=HTTPBasicAuth(username, password))
    print(f'code: {response.status_code}, {response.text}')


if __name__ == '__main__':
    upload_aar()
