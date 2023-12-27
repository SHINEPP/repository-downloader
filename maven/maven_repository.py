from requests.auth import HTTPBasicAuth


class MavenRepository:
    def __init__(self, host, user_name, password):
        self.url = host
        self.user_name = user_name
        self.password = password

    def http_basic_auth(self):
        if len(repository.user_name) > 0:
            return HTTPBasicAuth(self.user_name, self.password)
        return None


if __name__ == '__main__':
    import requests

    url = 'https://maven.cherrysoft.cn/repository/maven-releases/' + 'com/oh/bb/mmkv/develop-gp/9.5.1/develop-gp-9.5.1.module'
    repository = MavenRepository(url, 'develop', 'qwert12345')
    response = requests.get(repository.url, auth=repository.http_basic_auth())
    text = response.text
    print(text)
