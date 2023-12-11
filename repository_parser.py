if __name__ == '__main__':
    maven = 'https://dl.google.com/dl/android/maven2/'
    path = 'androidx.core:core-ktx:1.12.0'
    group, artifact, version = path.split(":")
    metadata = '/'.join(group.split('.')) + f'/{artifact}/maven-metadata.xml'
    print(f'{maven}/{metadata}')
