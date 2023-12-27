import re
import xml.etree.ElementTree as etree

from maven_dependency import MavenDependency


class MavenPom:
    def __init__(self, content: str):
        self.model_version = ''
        self.parent_group_id = ''
        self.parent_artifact_id = ''
        self.parent_version = ''
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self.packaging = ''
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
                        self.parent_group_id = node2.text.strip('[]')
                    elif node2.tag == ns + 'artifactId':
                        self.parent_artifact_id = node2.text.strip('[]')
                    elif node2.tag == ns + 'version':
                        self.parent_version = node2.text.strip('[]')
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


if __name__ == '__main__':
    pom_path = '../test/develop-gp-9.5.1.pom'
    with open(pom_path, 'r') as file:
        pom = MavenPom(file.read())
        print(f'pom = {pom.group_id}:{pom.artifact_id}:{pom.version}')
        print()
