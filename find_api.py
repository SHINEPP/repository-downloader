import os
import zipfile

if __name__ == '__main__':
    file_path = '/Users/zhouzhenliang/.gradle/caches/modules-2/files-2.1'
    for root, dirs, paths in os.walk(file_path):
        for path in paths:
            if path.endswith('.aar'):
                aar_path = os.path.join(root, path)
                with zipfile.ZipFile(aar_path, 'r') as zip_ref:
                    if 'assets/idc.json' in zip_ref.namelist():
                        print(aar_path)
