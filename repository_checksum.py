import hashlib
import os.path


def gen_check_sum(path: str):
    path1, path2 = os.path.splitext(path)

    # aar
    with open(path, 'rb') as file:
        buffer = file.read()
    md5 = hashlib.md5(buffer).hexdigest()
    sha1 = hashlib.sha1(buffer).hexdigest()
    sha256 = hashlib.sha256(buffer).hexdigest()
    with open(path + '.md5', 'w') as file:
        file.write(md5)
    with open(path + '.sha1', 'w') as file:
        file.write(sha1)
    with open(path + '.sha256', 'w') as file:
        file.write(sha256)

    # pom
    with open(path1 + '.pom', 'rb') as file:
        buffer = file.read()
    md5 = hashlib.md5(buffer).hexdigest()
    sha1 = hashlib.sha1(buffer).hexdigest()
    sha256 = hashlib.sha256(buffer).hexdigest()
    with open(path1 + '.pom.md5', 'w') as file:
        file.write(md5)
    with open(path1 + '.pom.sha1', 'w') as file:
        file.write(sha1)
    with open(path1 + '.pom.sha256', 'w') as file:
        file.write(sha256)


if __name__ == '__main__':
    gen_check_sum(
        '/Users/zhouzhenliang/Desktop/temp/topon_ad_gen/com/anythink/sdk/interstitial-tpn/6.4.18/interstitial-tpn-6.4.18.aar')
