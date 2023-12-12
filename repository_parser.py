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
        self.dependencies = []
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


class Implementation:
    def __init__(self, path):
        self.path = path
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.root_dir = ''
        self._parser()

    def maven_metadata_url(self):
        return self.root_dir + '/maven-metadata.xml'

    def maven_pom_url(self, metadata: MavenMetadata):
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


def download_file(url, local_path) -> bool:
    print(f'url: {url}')
    print(f'local_path: {local_path}')

    response = requests.get(url)
    print(f'code = {response.status_code}')
    if response.status_code == 200:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as file:
            file.write(response.content)
        return True
    return False


def test():
    maven_url = 'https://dl.google.com/dl/android/maven2'
    maven_path = '.m'
    metadata = 'maven-metadata.xml'
    fingerprint = ['md5', 'sha1', 'sha256', 'sha512']

    implementation = 'androidx.core:core-ktx:1.12.0'
    group, artifact, version = implementation.split(":")
    maven_dir = '/'.join(group.split('.')) + f'/{artifact}'

    metadata_url = f'{maven_url}/{maven_dir}/{metadata}'
    metadata_path = f'{maven_path}/{maven_dir}/{metadata}'

    # download_file(metadata_url, metadata_path)
    # for name in fingerprint:
    #     download_file(f'{metadata_url}.{name}', f'{metadata_path}.{name}')

    artifact_root_url = f'{maven_url}/{maven_dir}/{version}'
    artifact_root_path = f'{maven_path}/{maven_dir}/{version}'
    artifact_url = f'{artifact_root_url}/{artifact}-{version}.aar'
    artifact_path = f'{artifact_root_path}/{artifact}-{version}.aar'
    if download_file(artifact_url, artifact_path):
        for name in fingerprint:
            download_file(f'{artifact_url}.{name}', f'{artifact_path}.{name}')

        artifact_source_url = f'{artifact_root_url}/{artifact}-{version}-sources.jar'
        artifact_source_path = f'{artifact_root_path}/{artifact}-{version}-sources.jar'
        if download_file(artifact_source_url, artifact_source_path):
            for name in fingerprint:
                download_file(f'{artifact_url}.{name}', f'{artifact_path}.{name}')


if __name__ == '__main__':
    host = 'https://dl.google.com/dl/android/maven2/'

    imple = Implementation('androidx.core:core-ktx:1.12.0')
    metadata_url = imple.maven_metadata_url()
    metadata_resp = requests.get(host + metadata_url)
    if metadata_resp.status_code == 200:
        metadata = MavenMetadata(metadata_resp.text)
        pom_url = imple.maven_pom_url(metadata)
        print(host + pom_url)
        pom_resp = requests.get(host + pom_url)
        if pom_resp.status_code == 200:
            pom = MavenPom(pom_resp.text)
            print(pom)
