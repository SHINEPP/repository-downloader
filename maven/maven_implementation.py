class MavenImplementation:
    def __init__(self, path):
        self.path = path
        self.group_id = ''
        self.artifact_id = ''
        self.version = ''
        self._parser()

    def _parser(self):
        self.group_id, self.artifact_id, self.version = self.path.split(":")

    def group_path(self):
        return '/'.join(self.group_id.split('.'))

    def artifact_path(self):
        return f'{self.group_path()}/{self.artifact_id}'

    def version_path(self):
        return f'{self.artifact_path()}/{self.version}'

    def metadata_path(self):
        return f'{self.artifact_path()}/maven-metadata.xml'

    def pom_path(self):
        return f'{self.version_path()}/{self.artifact_id}-{self.version}.pom'

    def pom_sha1_path(self):
        return f'{self.pom_path()}.sha1'

    def aar_path(self):
        return f'{self.version_path()}/{self.artifact_id}-{self.version}.aar'

    def aar_sha1_path(self):
        return f'{self.aar_path()}.sha1'


if __name__ == '__main__':
    impl = MavenImplementation('com.clover.hdwallpapers.album:vyajpe:v30-jiagu')
    print(f'path = {impl.group_id}:{impl.artifact_id}:{impl.version}')
    print(f'maven_metadata_path = {impl.pom_path()}')
