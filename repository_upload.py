from xml.dom import minidom

import requests
from requests.auth import HTTPBasicAuth


def gen_pom(group_id_v: str, artifact_id_v: str, version_v: str, packaging_v: str, dependencies_v: list):
    doc = minidom.Document()
    project = doc.createElement('project')
    project.setAttribute('xmlns', 'http://maven.apache.org/POM/4.0.0')
    project.setAttribute('xsi:schemaLocation',
                         'http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd')
    project.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    doc.appendChild(project)
    model_version = doc.createElement('modelVersion')
    model_version.appendChild(doc.createTextNode('4.0.0'))
    project.appendChild(model_version)

    # 版本信息
    group_id = doc.createElement('groupId')
    group_id.appendChild(doc.createTextNode(group_id_v))
    project.appendChild(group_id)
    artifact_id = doc.createElement('artifactId')
    artifact_id.appendChild(doc.createTextNode(artifact_id_v))
    project.appendChild(artifact_id)
    version = doc.createElement('version')
    version.appendChild(doc.createTextNode(version_v))
    project.appendChild(version)
    packaging = doc.createElement('packaging')
    packaging.appendChild(doc.createTextNode(packaging_v))
    project.appendChild(packaging)

    # 依赖项
    if dependencies_v:
        dependencies = doc.createElement('dependencies')
        for dependency_v in dependencies_v:
            dependency = doc.createElement('dependency')
            items = ['groupId', 'artifactId', 'version', 'scope']
            keys = dependency_v.keys()
            for item in items:
                if item in keys:
                    group = doc.createElement(item)
                    group.appendChild(doc.createTextNode(dependency_v[item]))
                    dependency.appendChild(group)
            dependencies.appendChild(dependency)
        project.appendChild(dependencies)

    xml = doc.toprettyxml(indent='  ', newl='\n', encoding="utf-8")
    print(xml.decode())
    return xml


def upload_aar():
    group_id = 'com.shine.test66'
    artifact_id = 'alpha'
    version = '1.0.2'
    upload_repository_url = 'https://maven.cherrysoft.cn/service/rest/v1/components?repository=maven-releases'
    username = 'develop'
    password = '1234567890'

    aar_file_path = '/Users/zhouzhenliang/Desktop/temp/maven/develop-gp-10.7.2.0.aar'

    # 准备要上传的文件
    files = {
        'maven2.asset1': open(aar_file_path, 'rb'),
        'maven2.asset1.extension': (None, 'aar'),
        'maven2.asset2': gen_pom(group_id, artifact_id, version, 'aar', []),
        'maven2.asset2.extension': (None, 'pom'),
        'maven2.groupId': (None, group_id),
        'maven2.artifactId': (None, artifact_id),
        'maven2.version': (None, version),
    }

    # 通过 HTTP POST 上传 AAR 文件
    response = requests.post(upload_repository_url, files=files, auth=HTTPBasicAuth(username, password))

    print(f'code: {response.status_code}, {response.text}')


if __name__ == '__main__':
    # gen_pom('com.oh.ad.phonebatterydoctorssgp', 'develop-gp', "10.7.2.0", 'aar',
    #         [{'groupId': 'com.oh.ad.core', 'artifactId': 'develop', 'version': '10.7.2.1', 'scope': 'compile'}])
    upload_aar()
