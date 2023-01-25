#!/usr/bin/python3
# -*- coding:utf-8 -*-
# run via  python3 setup.py upload

import io, os, sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'kraken-rebalance-bot'
DESCRIPTION = 'A basic rebalance trading bot for the Kraken Cryptocurrency Exchange.'
URL = 'https://github.com/btschwertfeger/Kraken-Rebalance-Bot'
EMAIL = 'development@b-schwertfeger.de'
AUTHOR = 'Benjamin Thomas Schwertfeger'
REQUIRES_PYTHON = '>=3.7.0'
VERSION = '0.5.7.2'

REQUIRED = [
    'python-kraken-sdk',
    'schedule',
    'numpy',
    'requests',
]

EXTRAS = {
    #'testing': ['pytest', 'tqdm']
}

here = os.path.abspath(os.path.dirname(__file__))

try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f'\n{f.read()}'
except FileNotFoundError:
    long_description = DESCRIPTION

class UploadCommand(Command):

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        print(f'\033[1m{s}\033[0m')

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system(f'{sys.executable} setup.py sdist bdist_wheel --universal')

        self.status('Testing the build using flake8')
        if os.system('flake8 . --select=E9,F63,F7,F82 --show-source --statistics') != 0:
            self.status('Testing failed, build has some errors in it!')
            exit(1)

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        # self.status('Pushing git tags…')
        # os.system(f'git tag v{about['__version__']}')
        # os.system('git push --tags')

        sys.exit()

class TestUploadCommand(Command):
    '''Support setup.py test upload.'''

    description = 'Build and test publishing the package.'
    user_options = []

    @staticmethod
    def status(s):
        print(f'\033[1m{s}\033[0m')

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system(f'{sys.executable} setup.py sdist bdist_wheel --universal')

        self.status('Testing the build using flake8')
        if os.system('flake8 . --select=E9,F63,F7,F82 --show-source --statistics') != 0:
            self.status('Testing failed, build has some errors in it!')
            sys.exit(1)

        self.status('Uploading the package to test PyPI via Twine…')
        os.system('twine upload -r testpypi dist/*')#--repository-url https://test.pypi.org/legacy/ dist/*')

        sys.exit()

        
class TestCommand(Command):

    description = 'Build and test the package.'
    user_options = []

    @staticmethod
    def status(s):
        print(f'\033[1m{s}\033[0m')

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system(f'{sys.executable} setup.py sdist bdist_wheel --universal')

        self.status('Testing the build')
        if os.system('flake8 . --select=E9,F63,F7,F82 --show-source --statistics') != 0: exit(1)
        print('Success')
        sys.exit()

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*', '*.env*']),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['krakenRebalanceBot'],

    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='GPLv3',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: Unix'
    ],
    cmdclass={
        'upload': UploadCommand,
        'test': TestCommand,
        'testupload': TestUploadCommand,
    },
)
