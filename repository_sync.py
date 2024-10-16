import os
import re
import time
import xml.etree.ElementTree as etree

import requests
from requests.auth import HTTPBasicAuth

fingerprint = ['md5', 'sha1', 'sha256', 'sha512']


def maven_download_file(host: dict, local, path):
    print(f'download: {host["uri"]}{path}', end='')
    auth = None
    if 'credentials' in host.keys():
        credentials = host['credentials']
        if 'username' in credentials.keys() and 'password' in credentials.keys():
            username = credentials['username']
            password = credentials['password']
            if username and password:
                auth = HTTPBasicAuth(username, password)
    response = requests.get(os.path.join(host['uri'], path), auth=auth)
    if response.status_code == 200:
        local_path = local + path
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as file:
            file.write(response.content)
            print(' -> success')
        return response
    print(' -> fail')
    return None


class MavenMetadata:
    def __init__(self, content: str):
        self.group_id = ''
        self.artifact_id = ''
        self.latest_version = ''
        self.release_version = ''
        self.versions = []
        self.last_updated = ''
        self._parser(content)

    def _parser(self, content: str):
        root = etree.fromstring(content)
        for node in root:
            if node.tag == 'groupId':
                self.group_id = node.text
            elif node.tag == 'artifactId':
                self.artifact_id = node.text
            elif node.tag == 'versioning':
                for node1 in node:
                    if node1.tag == 'latest':
                        self.latest_version = node1.text.strip('[]')
                    elif node1.tag == 'release':
                        self.release_version = node1.text.strip('[]')
                    elif node1.tag == 'versions':
                        for node2 in node1:
                            if node2.tag == 'version':
                                self.versions.append(node2.text)
                    elif node1.tag == 'lastUpdated':
                        self.last_updated = node1.text


class MavenDependency:
    def __init__(self):
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.scope = ''


class MavenPom:
    def __init__(self, implementation, content: str):
        self.implementation = implementation
        self.model_version = ''
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.packaging = ''
        self.root_dir = ''
        self.dependencies: list[MavenDependency] = []
        self._parser(content)

    def _parser(self, content: str):
        root = etree.fromstring(content)
        ns = ''
        result = re.match(r'(\{.+}).+', root.tag)
        if result:
            ns = result.group(1)
        if root.tag != ns + 'project':
            return

        parent_group_id = ''
        parent_artifact_id = ''
        parent_version = ''
        for node1 in root:
            if node1.tag == ns + 'modelVersion':
                self.model_version = node1.text.strip('[]')
            elif node1.tag == ns + 'groupId':
                self.group_id = node1.text
            elif node1.tag == ns + 'artifactId':
                self.artifact_id = node1.text
            elif node1.tag == ns + 'version':
                self.version = node1.text.strip('[]')
            elif node1.tag == ns + 'packaging':
                self.packaging = node1.text
            elif node1.tag == ns + 'parent':
                for node2 in node1:
                    if node2.tag == ns + 'groupId':
                        parent_group_id = node2.text.strip('[]')
                    elif node2.tag == ns + 'artifactId':
                        parent_artifact_id = node2.text.strip('[]')
                    elif node2.tag == ns + 'version':
                        parent_version = node2.text.strip('[]')
            elif node1.tag == ns + 'dependencies':
                for node2 in node1:
                    if node2.tag == ns + 'dependency':
                        self._parser_artifact(ns, node2)
            elif node1.tag == ns + 'dependencyManagement':
                for node2 in node1:
                    if node2.tag == ns + 'dependencies':
                        for node3 in node2:
                            if node3.tag == ns + 'dependency':
                                self._parser_artifact(ns, node3)
        if len(self.packaging) == 0:
            self.packaging = 'jar'

        if len(self.group_id) == 0:
            self.group_id = parent_group_id
        if len(self.artifact_id) == 0:
            self.artifact_id = parent_artifact_id
        if len(self.version) == 0:
            self.version = parent_version

        if len(self.group_id) == 0:
            self.group_id = self.implementation.group_id
        if len(self.artifact_id) == 0:
            self.artifact_id = self.implementation.artifact_id
        if len(self.version) == 0:
            self.version = self.implementation.version
        self.root_dir = '/'.join(self.group_id.split('.')) + f'/{self.artifact_id}/{self.version}'

    def _parser_artifact(self, ns, node):
        deps = MavenDependency()
        for node1 in node:
            if node1.tag == ns + 'groupId':
                deps.group_id = node1.text
            elif node1.tag == ns + 'artifactId':
                deps.artifact_id = node1.text
            elif node1.tag == ns + 'version':
                deps.version = node1.text.strip('[]')
            elif node1.tag == ns + 'scope':
                deps.scope = node1.text
        if len(deps.group_id) > 0:
            self.dependencies.append(deps)

    def maven_artifact_path(self):
        return self.root_dir + '/' + self.artifact_id + '-' + self.version + '.' + self.packaging

    def maven_source_jar_path(self):
        return self.root_dir + '/' + self.artifact_id + '-' + self.version + '-sources.jar'


class Implementation:
    def __init__(self, path):
        self.path = path
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.root_dir = ''
        self._parser()

    def maven_metadata_path(self):
        return self.root_dir + '/maven-metadata.xml'

    def maven_pom_path(self, metadata: MavenMetadata):
        version = ''
        if len(self.version) == 0:
            if len(metadata.release_version) > 0:
                version = metadata.release_version
            elif len(metadata.latest_version) > 0:
                version = metadata.latest_version
        else:
            version = self.version
        return self.root_dir + '/' + version + '/' + self.artifact_id + '-' + version + '.pom'

    def _parser(self):
        self.group_id, self.artifact_id, self.version = self.path.split(":")
        self.root_dir = '/'.join(self.group_id.split('.')) + f'/{self.artifact_id}'


class ImplementationSyncer:

    def __init__(self, path):
        self.implementation = Implementation(path)
        self.metadata = None
        self.pom = None

    def _sync_metadata(self, host, local):
        metadata_path = self.implementation.maven_metadata_path()
        metadata_text = ''
        local_metadata = local + metadata_path
        if os.path.exists(local_metadata):
            modify_time = os.path.getmtime(local_metadata)
            cur_time = time.time().real
            if cur_time - modify_time > 10 * 60:
                with open(local_metadata, 'r') as file:
                    metadata_text = file.read()
        if len(metadata_text) == 0:
            metadata_resp = maven_download_file(host, local, metadata_path)
            if metadata_resp:
                metadata_text = metadata_resp.text
                for name in fingerprint:
                    maven_download_file(host, local, metadata_path + '.' + name)
        if len(metadata_text) > 0:
            self.metadata = MavenMetadata(metadata_text)

    def _sync_pom(self, host, local):
        self._sync_metadata(host, local)
        if not self.metadata:
            return
        pom_path = self.implementation.maven_pom_path(self.metadata)
        pom_text = ''
        local_pom = local + pom_path
        if os.path.exists(local_pom):
            with open(local_pom, 'r') as file:
                pom_text = file.read()
        if len(pom_text) == 0:
            pom_resp = maven_download_file(host, local, pom_path)
            if pom_resp:
                pom_text = pom_resp.text
                for name in fingerprint:
                    maven_download_file(host, local, pom_path + '.' + name)
        if len(pom_text) > 0:
            self.pom = MavenPom(self.implementation, pom_text)

    def sync_artifact(self, host, local) -> bool:
        self._sync_pom(host, local)
        if not self.pom:
            return False
        artifact_path = self.pom.maven_artifact_path()
        local_artifact = local + artifact_path
        if os.path.exists(local_artifact):
            return True
        artifact_resp = maven_download_file(host, local, artifact_path)
        if artifact_resp:
            for name in fingerprint:
                maven_download_file(host, local, artifact_path + '.' + name)
            source_jar_url = self.pom.maven_source_jar_path()
            source_jar_resp = maven_download_file(host, local, source_jar_url)
            if source_jar_resp:
                for name in fingerprint:
                    maven_download_file(host, local, source_jar_url + '.' + name)
            return True
        return False


class Syncer:
    def __init__(self, hosts: list, local_dir: str, sync_den: bool = True):
        self.paths = []
        self.hosts = hosts
        self.local_dir = local_dir
        self.sync_den = sync_den

    def start_sync(self, path):
        if path in self.paths:
            return
        print(f'sync: {path}')
        self.paths.append(path)
        sync = ImplementationSyncer(path)
        for host in self.hosts:
            if sync.sync_artifact(host, self.local_dir):
                if not self.sync_den:
                    continue
                for depe in sync.pom.dependencies:
                    depe_path = depe.group_id + ':' + depe.artifact_id + ':' + depe.version
                    self.start_sync(depe_path)
                break


if __name__ == '__main__':
    maven_hosts = [
        {'uri': 'https://dl.google.com/dl/android/maven2/'},
        {'uri': 'https://repo1.maven.org/maven2/'},
        {'uri': 'https://jcenter.bintray.com/'},
        {'uri': 'https://jitpack.io/'},
        {'uri': 'https://maven.aliyun.com/repository/google/'},
        {'uri': 'https://maven.aliyun.com/repository/public/'},
        {
            'uri': 'https://maven.cherrysoft.cn/repository/maven-releases/',
            'credentials': {
                'username': 'develop',
                'password': 'qwert12345'
            }
        }
    ]

    syncer = Syncer(hosts=maven_hosts, local_dir='./.m/', sync_den=False)
    syncer.start_sync('com.oh.tinker.tinker-android:tinker-android-lib:1.0.1')

    # start_sync('eu.davidea:flexible-adapter:5.1.0', sync_den=False)
    # start_sync('eu.davidea:flexible-adapter-ui:1.0.0')
    # start_sync('eu.davidea:flexible-adapter-livedata:1.0.0-b3')
    # start_sync('eu.davidea:flexible-adapter-databinding:1.0.0')
