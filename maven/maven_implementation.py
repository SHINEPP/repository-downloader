class MavenImplementation:
    def __init__(self, path):
        self.path = path
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self._parser()

    def _parser(self):
        self.group_id, self.artifact_id, self.version = self.path.split(":")

    def maven_metadata_path(self):
        return '/'.join(self.group_id.split('.')) + f'/{self.artifact_id}' + '/maven-metadata.xml'


if __name__ == '__main__':
    impl = MavenImplementation('com.google.ads.mediation:mintegral:16.5.21.0')
    print(f'path = {impl.group_id}:{impl.artifact_id}:{impl.version}')
    print(f'maven_metadata_path = {impl.maven_metadata_path()}')
