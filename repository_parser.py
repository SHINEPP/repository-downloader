import os

import requests

if __name__ == '__main__':
    maven_url = 'https://dl.google.com/dl/android/maven2/'
    maven_path = '.m'
    metadata = 'maven-metadata.xml'

    path = 'androidx.core:core-ktx:1.12.0'
    group, artifact, version = path.split(":")
    maven_dir = '/'.join(group.split('.')) + f'/{artifact}'

    metadata_url = f'{maven_url}/{maven_dir}/{metadata}'
    metadata_path = f'{maven_path}/{maven_dir}/{metadata}'
    print(metadata_url)
    print(metadata_path)

    metadata_file = requests.get(metadata_url)
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, 'wb') as file:
        file.write(metadata_file.content)
