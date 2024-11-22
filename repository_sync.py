from __future__ import annotations

import os
import re
import time
import xml.etree.ElementTree as etree

import requests
from requests import Response
from requests.auth import HTTPBasicAuth


def maven_download_file(host: dict, store_dir: str, relative_path: str) -> Response | None:
    """
    下载maven仓库中文件
    :param host: maven仓库源信息
    :param store_dir: 本地存储根目录
    :param relative_path: 文件相对地址
    :return: Response | None
    """
    print(f'download: {host["uri"]}{relative_path}', end='')
    auth = None
    if 'credentials' in host.keys():
        credentials = host['credentials']
        credentials_keys = credentials.keys()
        if 'username' in credentials_keys and 'password' in credentials_keys:
            username = credentials['username']
            password = credentials['password']
            if username and password:
                auth = HTTPBasicAuth(username, password)

    response = requests.get(os.path.join(host['uri'], relative_path), auth=auth)
    success = False
    if response.status_code == 200:
        local_path = os.path.join(store_dir, relative_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as file:
            file.write(response.content)
            success = True

    if success:
        print(' -> success')
        return response
    else:
        print(' -> fail')
        return None


def maven_download_files(hosts: list, store_dir: str, relative_path: str) -> Response | None:
    """
    下载maven仓库中文件和md5, sha1, sha256, sh512
    """
    fingerprint = ['md5', 'sha1', 'sha256', 'sha512']
    response = None
    for host in hosts:
        response = maven_download_file(host, store_dir, relative_path)
        if response:
            for name in fingerprint:
                maven_download_file(host, store_dir, relative_path + '.' + name)
            break
    if not response:
        print(f'error: download fail {relative_path}')
    return response


class MavenHost:
    """
    Maven 信息
    """

    def __init__(self, hosts: list, store_dir: str):
        self.hosts = hosts
        self.store_dir = store_dir


class MavenDependency:
    """
    Maven 依赖信息
    """

    def __init__(self):
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.scope = ''


class MavenMetadata:
    """
    Maven Metadata sync & parser
    """

    def __init__(self, host: MavenHost, metadata_path: str):
        self.host = host
        self.metadata_path = metadata_path
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.latest_version = ''
        self.release_version = ''
        self.versions = []
        self.last_updated = ''

    def sync(self, is_download: bool = True) -> bool:
        metadata_text = ''
        local_metadata = os.path.join(self.host.store_dir, self.metadata_path)
        if os.path.exists(local_metadata):
            modify_time = os.path.getmtime(local_metadata)
            cur_time = time.time().real
            if cur_time - modify_time < 1000 * 60:
                with open(local_metadata, 'r') as file:
                    metadata_text = file.read()
        if is_download and len(metadata_text) == 0:
            metadata_resp = maven_download_files(self.host.hosts, self.host.store_dir, self.metadata_path)
            if metadata_resp:
                metadata_text = metadata_resp.text
        if len(metadata_text) > 0:
            return self._parser_metadata(metadata_text)
        else:
            return False

    def _parser_metadata(self, content: str) -> bool:
        root = etree.fromstring(content)
        if root.tag != 'metadata':
            return False
        for node in root:
            text = node.text.strip()
            if node.tag == 'groupId':
                self.group_id = text
            elif node.tag == 'artifactId':
                self.artifact_id = text
            elif node.tag == 'version':
                self.version = text
            elif node.tag == 'versioning':
                for node1 in node:
                    text1 = node1.text.strip()
                    if node1.tag == 'latest':
                        self.latest_version = text1.strip('[]')
                    elif node1.tag == 'release':
                        self.release_version = text1.strip('[]')
                    elif node1.tag == 'versions':
                        for node2 in node1:
                            text2 = node2.text.strip()
                            if node2.tag == 'version':
                                self.versions.append(text2.strip('[]'))
                    elif node1.tag == 'lastUpdated':
                        self.last_updated = text1
        return True


class MavenPom:
    """
    Maven Pom文件信息&处理
    """

    def __init__(self, host: MavenHost, pom_path: str, synced_poms: list[str] | None = None):
        self.host = host
        self.pom_path = pom_path
        self.synced_poms = synced_poms
        self.model_version = ''
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.packaging = ''
        self.root_dir = ''
        self.parent_pom: MavenPom | None = None
        self.properties = {str: str}
        self._dependencies: list[MavenDependency] = []

    def sync(self, is_download: bool = True) -> bool:
        # 防止pom parent死循环
        if self.synced_poms:
            if self.pom_path in self.synced_poms:
                return False
            self.synced_poms.append(self.pom_path)

        pom_text = ''
        local_pom = os.path.join(self.host.store_dir, self.pom_path)
        if os.path.exists(local_pom):
            with open(local_pom, 'r') as file:
                pom_text = file.read()
        if is_download and len(pom_text) == 0:
            pom_resp = maven_download_files(self.host.hosts, self.host.store_dir, self.pom_path)
            if pom_resp:
                pom_text = pom_resp.text
        if len(pom_text) > 0:
            return self._parser(pom_text, is_download)
        else:
            return False

    def _parser(self, content: str, is_download: bool = True) -> bool:
        try:
            root = etree.fromstring(content)
        except Exception as e:
            print(e)
            return False

        ns = ''
        result = re.match(r'(\{.+}).+', root.tag)
        if result:
            ns = result.group(1)
        if root.tag != ns + 'project':
            return False

        parent_group_id = ''
        parent_artifact_id = ''
        parent_version = ''

        # 因为集成关系优先解析parent
        for node1 in root:
            if node1.tag == ns + 'parent':
                for node2 in node1:
                    if not node2.text:
                        continue
                    text2 = node2.text.strip()
                    if node2.tag == ns + 'groupId':
                        parent_group_id = text2
                    elif node2.tag == ns + 'artifactId':
                        parent_artifact_id = text2
                    elif node2.tag == ns + 'version':
                        parent_version = text2.strip('[]')
                if len(parent_group_id) > 0 and len(parent_artifact_id) > 0:
                    path = f'{parent_group_id}:{parent_artifact_id}:{parent_version}'
                    impl = MavenImplementation(self.host, path)
                    impl.sync_metadata()
                    if impl.sync_pom(is_download=is_download, synced_poms=self.synced_poms):
                        self.parent_pom = impl.pom

        self.group_id = parent_group_id
        self.artifact_id = parent_artifact_id
        self.version = parent_version

        # properties
        self.properties.clear()
        self.properties['project.groupId'] = self.group_id
        self.properties['project.artifactId'] = self.artifact_id
        self.properties['project.version'] = self.version
        for node1 in root:
            if node1.tag == ns + 'properties':
                for node2 in node1:
                    text2 = node2.text
                    if node2.tag and text2:
                        self.properties[node2.tag[len(ns):]] = node2.text.strip()

        for node1 in root:
            text = node1.text
            if not text:
                text = ''
            text = self._parser_node_text(text.strip())
            if node1.tag == ns + 'modelVersion':
                self.model_version = text
            elif node1.tag == ns + 'groupId':
                self.group_id = text
                self.properties['project.groupId'] = self.group_id
            elif node1.tag == ns + 'artifactId':
                self.artifact_id = text
                self.properties['project.artifactId'] = self.artifact_id
            elif node1.tag == ns + 'version':
                self.version = text.strip('[]')
                self.properties['project.version'] = self.version
            elif node1.tag == ns + 'packaging':
                self.packaging = text
            elif node1.tag == ns + 'dependencies':
                for node2 in node1:
                    if node2.tag == ns + 'dependency':
                        self._parser_dependency(ns, node2)
            elif node1.tag == ns + 'dependencyManagement':
                for node2 in node1:
                    if node2.tag == ns + 'dependencies':
                        for node3 in node2:
                            if node3.tag == ns + 'dependency':
                                self._parser_dependency(ns, node3)

        if len(self.group_id) == 0 or len(self.artifact_id) == 0:
            return False

        self.root_dir = os.sep.join(self.group_id.split('.') + [self.artifact_id, self.version])
        return True

    def _parser_dependency(self, ns, node):
        deps = MavenDependency()
        for node1 in node:
            text = self._parser_node_text(node1.text.strip())
            if node1.tag == ns + 'groupId':
                deps.group_id = text
            elif node1.tag == ns + 'artifactId':
                deps.artifact_id = text
            elif node1.tag == ns + 'version':
                deps.version = text.strip('[]')
            elif node1.tag == ns + 'scope':
                deps.scope = text
        if len(deps.group_id) > 0 and len(deps.artifact_id) > 0:
            self._dependencies.append(deps)

    def _parser_node_text(self, text):
        if not text:
            return ''
        result = re.match(r'\$\{(.+)}', text)
        if result:
            key = result.group(1)
            if key in self.properties.keys():
                value = self.properties[key]
            else:
                value = None
            parent = self.parent_pom
            while parent is not None and value is None:
                if key in parent.properties.keys():
                    value = parent.properties[key]
                parent = parent.parent_pom
            if value:
                return value
        return text

    def maven_dependencies(self) -> list[MavenDependency]:
        deps = []
        if self.parent_pom:
            dep_list = self.parent_pom.maven_dependencies()
            if dep_list:
                for dep in dep_list:
                    deps.append(dep)
        for dep in self._dependencies:
            deps.append(dep)
        return deps

    def maven_artifact_path(self):
        if self.packaging == 'aar' or self.packaging == 'pom':
            artifact = self.packaging
        else:
            artifact = 'jar'
        return os.path.join(self.root_dir, self.artifact_id + '-' + self.version + '.' + artifact)

    def maven_source_jar_path(self):
        return os.path.join(self.root_dir, self.artifact_id + '-' + self.version + '-sources.jar')


class MavenImplementation:
    """
    Maven Implementation解析
    """

    def __init__(self, host: MavenHost, value: str):
        self.host = host
        self.value = value
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.root_dir = ''
        self.metadata_path = ''
        self.metadata: MavenMetadata | None = None
        self.pom: MavenPom | None = None
        self._parser()

    def _parser(self):
        self.group_id, self.artifact_id, self.version = self.value.split(":")
        assert len(self.group_id) > 0 and len(self.artifact_id) > 0
        self.root_dir = os.sep.join(self.group_id.split('.') + [self.artifact_id])
        self.metadata_path = os.path.join(self.root_dir, 'maven-metadata.xml')

    def sync_metadata(self, is_download: bool = True) -> bool:
        metadata = MavenMetadata(self.host, self.metadata_path)
        if metadata.sync(is_download):
            self.metadata = metadata
            return True
        return False

    def sync_pom(self, is_download: bool = True, synced_poms: list[str] | None = None) -> bool:
        pom_path = self._pom_path()
        if pom_path:
            pom = MavenPom(self.host, pom_path, synced_poms)
            if pom.sync(is_download):
                self.pom = pom
                return True
        return False

    def _pom_path(self):
        version = None
        if len(self.version) > 0:
            version = self.version
        elif self.metadata:
            if len(self.metadata.release_version) > 0:
                version = self.metadata.release_version
            elif len(self.metadata.latest_version) > 0:
                version = self.metadata.latest_version
            elif len(self.metadata.version) > 0:
                version = self.metadata.version
        if version:
            return os.sep.join([self.root_dir, version, self.artifact_id + '-' + version + '.pom'])
        else:
            return None

    def sync_artifact(self) -> bool:
        if not self.pom:
            return False
        artifact_path = self.pom.maven_artifact_path()
        local_artifact = os.path.join(self.host.store_dir, artifact_path)
        if os.path.exists(local_artifact):
            return True
        artifact_resp = maven_download_files(self.host.hosts, self.host.store_dir, artifact_path)
        if artifact_resp:
            source_jar_url = self.pom.maven_source_jar_path()
            maven_download_files(self.host.hosts, self.host.store_dir, source_jar_url)
            return True
        return False


class MavenSyncer:
    def __init__(self, host: MavenHost, sync_depe: bool = True):
        self.host = host
        self.sync_depe = sync_depe
        self.paths = []

    def sync(self, path: str):
        self._sync(path, 0)

    def _sync(self, path: str, deep: int):
        print(f'sync: {path}')
        # 解决依赖环
        if path in self.paths:
            return
        self.paths.append(path)
        impl = MavenImplementation(self.host, path)
        impl.sync_metadata()
        impl.sync_pom()
        impl.sync_artifact()
        if impl.pom and self.sync_depe:
            depe_list = impl.pom.maven_dependencies()
            if depe_list:
                for depe in depe_list:
                    depe_path = ":".join([depe.group_id, depe.artifact_id, depe.version])
                    self._sync(depe_path, deep + 1)


class DependencyPrinter:
    def __init__(self, host: MavenHost):
        self.host = host
        self.paths = []
        self.tags = []

    def print(self, path: str):
        self.prints([path])

    def prints(self, paths: list[str]):
        print('dependency')
        for path in paths:
            self.tags.clear()
            self._print(path, 0, path == paths[-1])

    def _print(self, path: str, deep: int, is_last: bool):
        if len(path) == 0:
            name = '(?)'
            is_finished = True
        elif path in self.paths:
            name = f'{path} (*)'
            is_finished = True
        else:
            name = path
            is_finished = False

        if is_last:
            tag = '\\--- '
        else:
            tag = '+--- '
        print(''.join(self.tags) + tag + name)

        if is_finished:
            return

        self.paths.append(path)
        impl = MavenImplementation(self.host, path)
        impl.sync_metadata(False)
        impl.sync_pom(is_download=False)

        if not impl.pom:
            if is_last:
                self.tags.append(' ' * 5)
            else:
                self.tags.append('|' + ' ' * 4)
            self._print('', deep + 1, True)
            self.tags.pop()
            return

        depe_list = impl.pom.maven_dependencies()
        for depe in depe_list:
            last = depe == depe_list[-1]
            depe_path = ":".join([depe.group_id, depe.artifact_id, depe.version])
            if is_last:
                self.tags.append(' ' * 5)
            else:
                self.tags.append('|' + ' ' * 4)
            self._print(depe_path, deep + 1, last)
            self.tags.pop()


if __name__ == '__main__':
    maven_hosts = [
        {'uri': 'https://maven.google.com/'},
        {'uri': 'https://dl.google.com/dl/android/maven2/'},
        {'uri': 'https://repo1.maven.org/maven2/'},
        {'uri': 'https://jcenter.bintray.com/'},
        {'uri': 'https://jitpack.io/'},
        {'uri': 'https://maven.scijava.org/content/repositories/public/'},
        {'uri': 'https://jfrog.anythinktech.com/artifactory/overseas_sdk/'},
        {'uri': 'https://dl-maven-android.mintegral.com/repository/mbridge_android_sdk_oversea/'},
        {'uri': 'https://maven.scijava.org/content/repositories/public/'},
        {'uri': 'https://maven.aliyun.com/repository/google/'},
        {'uri': 'https://maven.aliyun.com/repository/public/'},
        {'uri': 'https://mvnrepository.com/'},
        {
            'uri': 'https://maven.cherrysoft.cn/repository/maven-releases/',
            'credentials': {
                'username': 'develop',
                'password': '12345'
            }
        }
    ]

    storage = '/Volumes/WDDATA/maven/repository'
    syncer = MavenSyncer(MavenHost(hosts=maven_hosts, store_dir=storage), sync_depe=True)
    # syncer.sync('com.google.code.gson:gson:2.8.9')
    # syncer.sync('com.github.Harbor2:emlibrary:v2.2.4')
    # syncer.sync('org.greenrobot:eventbus:3.2.0')
    # syncer.sync('com.airbnb.android:lottie:6.1.0')
    # syncer.sync('jp.wasabeef:glide-transformations:4.3.0')
    # syncer.sync('com.github.bumptech.glide:glide:4.15.1')
    # syncer.sync('eu.davidea:flexible-adapter-ui:1.0.0')
    # syncer.sync('eu.davidea:flexible-adapter:5.1.0')

    printer = DependencyPrinter(MavenHost(hosts=maven_hosts, store_dir=storage))
    printer.prints([
        'eu.davidea:flexible-adapter:5.1.0',
        'eu.davidea:flexible-adapter-ui:5.1.0'])
