import hashlib
import os.path


def gen_check_files(path: str):
    with open(path, 'rb') as file:
        buffer = file.read()
    with open(path + '.md5', 'w') as file:
        file.write(hashlib.md5(buffer).hexdigest())
    with open(path + '.sha1', 'w') as file:
        file.write(hashlib.sha1(buffer).hexdigest())
    with open(path + '.sha256', 'w') as file:
        file.write(hashlib.sha256(buffer).hexdigest())


def gen_check_sum(path: str):
    path1, path2 = os.path.splitext(path)
    gen_check_files(path)
    gen_check_files(path1 + '.pom')
    gen_check_files(os.path.join(os.path.dirname(os.path.dirname(path)), 'maven-metadata.xml'))


if __name__ == '__main__':
    gen_check_sum(
        '/Users/zhouzhenliang/Desktop/temp/topon_log/com/anythink/sdk/interstitial-tpn-alpha/6.4.17/interstitial-tpn-alpha-6.4.17.aar')
