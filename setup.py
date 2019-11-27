from setuptools import setup, find_packages

long_description = open('README.md').read()

setup(
    name='tm-editor',
    version='0.11.0',
    description="CMS Level-1 Trigger Menu Editor",
    long_description=long_description,
    author = "Bernhard Arnold",
    author_email = "bernhard.arnold@cern.ch",
    url = "http://globaltrigger.hephy.at/upgrade/tme",
    packages = find_packages(),
    install_requires=[
        'tm-python @ git+https://github.com/cms-l1-globaltrigger/tm-python@0.7.3',
        'Markdown>=3.1',
        'PyQt5>=5.13'
    ],
    entry_points={
        'console_scripts': [
            'tm-editor = tmEditor.__main__:main',
        ],
    },
    test_suite='tests',
    license='GPLv3'
)
