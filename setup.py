# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='templaty',
    version='1.3.1',
    description='Generate programming code from template files',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/samvv/Templaty',
    author='Sam Vervaeck',
    author_email='vervaeck.sam@skynet.be',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Generators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='template code-generator c++ c php java python',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3.5, <4',
    install_requires=['gast'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    entry_points={
        'console_scripts': [
            'templaty=templaty:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/samvv/Templaty/issues',
        'Source': 'https://github.com/samvv/Templaty/',
    },
)
