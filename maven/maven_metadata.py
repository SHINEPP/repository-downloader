import xml.etree.ElementTree as etree


# 解析 maven-metadata.xml
class MavenMetadata:
    def __init__(self, content: str):
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
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
            elif node.tag == 'version':
                self.version = node.text.strip('[]')
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


if __name__ == '__main__':
    metadata_path = '../test/maven-metadata.xml'
    with open(metadata_path, 'r') as file:
        text = file.read()
        metadata = MavenMetadata(text)
        print(f'metadata = {metadata.group_id}')
