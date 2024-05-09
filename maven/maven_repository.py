from requests.auth import HTTPBasicAuth


class MavenRepository:
    def __init__(self, url, user_name, password):
        self.url = url
        self.user_name = user_name
        self.password = password

    def http_basic_auth(self):
        if len(repository.user_name) > 0:
            return HTTPBasicAuth(self.user_name, self.password)
        return None


if __name__ == '__main__':
    import os
    import requests
    import hashlib
    from maven_implementation import MavenImplementation

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
