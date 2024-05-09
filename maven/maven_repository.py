from requests.auth import HTTPBasicAuth


class MavenRepository:
    def __init__(self, url, user_name, password):
        self.url = url
        self.user_name = user_name
        self.password = password

    def http_basic_auth(self):
        if len(self.user_name) > 0:
            return HTTPBasicAuth(self.user_name, self.password)
        return None


if __name__ == '__main__':
    resp_url = 'https://packages.aliyun.com/maven/repository/2279663-release-AiyNZM'
    repository = MavenRepository(resp_url, '621344be8af5d39eb3f17f3e', '(ijI1DwR7[wG')
