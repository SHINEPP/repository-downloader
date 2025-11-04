import os
from xml.dom import minidom

import requests
from requests.auth import HTTPBasicAuth

XML_NAMESPACE = 'http://maven.apache.org/POM/4.0.0'
XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'
XSI_SCHEMA_LOCATION = 'http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd'


def create_maven_pom(group_id_v: str, artifact_id_v: str, version_v: str, packaging_v: str,
                     dependencies_v: list) -> bytes:
    """
    创建maven pom文件
    """
    doc = minidom.Document()
    # project attribute
    project = doc.createElement('project')
    project.setAttribute('xsi:schemaLocation', XSI_SCHEMA_LOCATION)
    project.setAttribute('xmlns', XML_NAMESPACE)
    project.setAttribute('xmlns:xsi', XSI_NAMESPACE)
    doc.appendChild(project)

    # model version
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

    return doc.toprettyxml(indent='  ', newl='\n', encoding="utf-8")


def upload_aar(group_id: str, artifact_id: str, version: str, aar_path: str, pom_path: str):
    repository_url = 'https://maven.cherrysoft.cn/service/rest/v1/components?repository=mediation-sdk'
    username = 'develop'
    password = 'qwert12345'

    artifact_file = open(aar_path, 'rb')
    pom_file = open(pom_path, 'rb')

    # 准备要上传的文件
    files = {
        'maven2.asset1': artifact_file,
        'maven2.asset1.extension': (None, 'aar'),
        'maven2.asset2': pom_file,
        'maven2.asset2.extension': (None, 'pom'),
        'maven2.groupId': (None, group_id),
        'maven2.artifactId': (None, artifact_id),
        'maven2.version': (None, version),
    }

    # 通过 HTTP POST 上传 AAR 文件
    response = requests.post(repository_url, files=files, auth=HTTPBasicAuth(username, password))
    print(f'code: {response.status_code}, {response.text}')


def upload_aars():
    m_path = '.m/'
    for root, dirs, files in os.walk(m_path):
        root_dir = root[len(m_path):]
        for file in files:
            if file.endswith('.aar'):
                aar_path = m_path + os.path.join(root_dir, file)
                pom_path = m_path + os.path.join(root_dir, file.replace('.aar', '.pom'))

                paths = root_dir.split('/')
                version = paths[len(paths) - 1]
                artifact_id = paths[len(paths) - 2]
                group_id = '.'.join(paths[:len(paths) - 2])
                print(f'version = {version}')
                print(f'artifact_id = {artifact_id}')
                print(f'group_id = {group_id}')
                print(f'aar_path = {aar_path}')
                print(f'pom_path = {pom_path}')
                upload_aar(group_id, artifact_id, version, aar_path, pom_path)


if __name__ == '__main__':
    upload_aars()
