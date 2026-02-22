from setuptools import setup, find_packages

setup(
    name='duprly',
    version='0.2.0',
    author='Leo',
    author_email='lsternlicht@gmail.com',
    description='A utility to download and process DUPR data.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lsternlicht/duprly',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'duprly': ['datasette_templates/*.html'],
    },
    install_requires=[
        'sqlalchemy',
        'loguru',
        'click',
        'rich',
        'rich-click',
        'requests',
        'openpyxl',
        'python-dotenv',
        'tqdm',
        'prompt-toolkit',
        'browser-cookie3',
        'setuptools<81',
        'datasette',
        'datasette-vega',
        'sqlite-utils'
    ],
    entry_points={
        'console_scripts': [
            'duprly=duprly.cli:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
