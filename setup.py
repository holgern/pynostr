import setuptools


def read_requirements(file):
    with open(file) as f:
        return f.read().splitlines()


with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = read_requirements("requirements.txt")

setuptools.setup(
    name='pynostr',
    packages=setuptools.find_packages(exclude=['tests']),
    version='0.0.1',
    description='Python Library for nostr.',
    author='Holger Nahrstaedt',
    author_email='nahrstaedt@gmail.com',
    url='https://github.com/holgern/pynostr',
    keywords=['nostr'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
    ],
    install_requires=requirements,
    license='MIT license',
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'pynostr=pynostr.cli:main',
        ]
    },
)
