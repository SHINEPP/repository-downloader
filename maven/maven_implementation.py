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
    import os
    import requests
    import hashlib
    from maven_repository import MavenRepository

    resp_url = 'https://packages.aliyun.com/maven/repository/2279663-release-AiyNZM'
    repository = MavenRepository(resp_url, '621344be8af5d39eb3f17f3e', '(ijI1DwR7[wG')
    impl = MavenImplementation('com.clover.hdwallpapers.album:vyajpe:v30-jiagu')

    pom_url = f'{resp_url}/{impl.pom_path()}'
    print(f'pom_url = {pom_url}')
    response = requests.get(pom_url, auth=repository.http_basic_auth())
    file_path = f'../.m/{impl.pom_path()}'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    pom_sha1 = hashlib.new("sha1", response.content).hexdigest()
    print(f'pom_sha1 = {pom_sha1}')

    pom_sha1_url = f'{resp_url}/{impl.pom_sha1_path()}'
    print(f'pom_sha1_url = {pom_sha1_url}')
    response = requests.get(pom_sha1_url, auth=repository.http_basic_auth())
    text = response.text
    print(text)

    aar_url = f'{resp_url}/{impl.aar_path()}'
    print(f'aar_url = {aar_url}')
    response = requests.get(aar_url, auth=repository.http_basic_auth())
    file_path = f'../.m/{impl.aar_path()}'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    aar_sha1 = hashlib.new("sha1", response.content).hexdigest()
    print(f'aar_sha1 = {aar_sha1}')

    aar_sha1_url = f'{resp_url}/{impl.aar_sha1_path()}'
    print(f'aar_sha1_url = {aar_sha1_url}')
    response = requests.get(aar_sha1_url, auth=repository.http_basic_auth())
    text = response.text
    print(text)
