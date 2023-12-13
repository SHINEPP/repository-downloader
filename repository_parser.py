import os
import re
import xml.etree.ElementTree as etree

import requests


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
                        self.latest_version = node1.text
                    elif node1.tag == 'release':
                        self.release_version = node1.text
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
    def __init__(self, content: str):
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
        result = re.match(r'(\{.+\}).+', root.tag)
        if result:
            ns = result.group(1)
        if root.tag != ns + 'project':
            return
        for node1 in root:
            if node1.tag == ns + 'modelVersion':
                self.model_version = node1.text
            elif node1.tag == ns + 'groupId':
                self.group_id = node1.text
            elif node1.tag == ns + 'artifactId':
                self.artifact_id = node1.text
            elif node1.tag == ns + 'version':
                self.version = node1.text
            elif node1.tag == ns + 'packaging':
                self.packaging = node1.text
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
        self.root_dir = '/'.join(self.group_id.split('.')) + f'/{self.artifact_id}/{self.version}'

    def _parser_artifact(self, ns, node):
        deps = MavenDependency()
        for node1 in node:
            if node1.tag == ns + 'groupId':
                deps.group_id = node1.text
            elif node1.tag == ns + 'artifactId':
                deps.artifact_id = node1.text
            elif node1.tag == ns + 'version':
                deps.version = node1.text
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


def download_file(host, path):
    print(f'download_file(), url = {host}{path}')
    response = requests.get(host + path)
    if response.status_code == 200:
        local_path = maven_local_dir + path
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as file:
            file.write(response.content)
        return response
    return None


class SyncImplementation:

    def __init__(self, path):
        self.implementation = Implementation(path)
        self.metadata = None
        self.pom = None

    def _sync_metadata(self, host):
        metadata_url = self.implementation.maven_metadata_path()
        metadata_resp = download_file(host, metadata_url)
        if metadata_resp:
            self.metadata = MavenMetadata(metadata_resp.text)

    def _sync_pom(self, host):
        if self.implementation:
            pom_url = self.implementation.maven_pom_path(self.metadata)
            pom_resp = download_file(host, pom_url)
            if pom_resp:
                self.pom = MavenPom(pom_resp.text)
                for name in fingerprint:
                    download_file(host, pom_url + '.' + name)

    def start_sync(self, host):
        self._sync_metadata(host)
        pom_path = self.implementation.maven_pom_path(self.metadata)
        if os.path.exists(maven_local_dir + pom_path):
            return

        self._sync_pom(host)
        if not self.pom:
            return

        # artifact
        artifact_url = self.pom.maven_artifact_path()
        artifact_resp = download_file(host, artifact_url)
        if artifact_resp:
            for name in fingerprint:
                download_file(host, artifact_url + '.' + name)
            source_jar_url = self.pom.maven_source_jar_path()
            source_jar_resp = download_file(host, source_jar_url)
            if source_jar_resp:
                for name in fingerprint:
                    download_file(host, source_jar_url + '.' + name)


def start_sync(path):
    sync = SyncImplementation(path)
    sync.start_sync(maven_host)
    if sync.pom:
        for depe in sync.pom.dependencies:
            depe_path = depe.group_id + ':' + depe.artifact_id + ':' + depe.version
            start_sync(depe_path)


if __name__ == '__main__':
    fingerprint = ['md5', 'sha1', 'sha256', 'sha512']
    maven_host = 'https://dl.google.com/dl/android/maven2/'
    maven_local_dir = '.m/'
    start_sync('androidx.core:core-ktx:1.12.0')
