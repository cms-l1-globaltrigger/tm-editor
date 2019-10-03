from setuptools import setup

setup(
    name = 'tm-editor',
    version = '0.10.0',
    description = "CMS Level-1 Trigger Menu Editor",
    author = "Bernhard Arnold",
    author_email = "bernhard.arnold@cern.ch",
    url = "https://github.com/cms-l1-globaltrigger/tm-editor/",
    packages = [
        'tmEditor',
        'tmEditor.core',
        'tmEditor.gui',
        'tmEditor.gui.models',
        'tmEditor.gui.proxies',
        'tmEditor.gui.views',
    ],
    package_data={},
    install_requires=[
        'tm-table>=0.7.3',
        'tm-grammar>=0.7.3',
        'tm-eventsetup>=0.7.3',
        'PyQt5>=5.13',
    ],
    entry_points={
        'console_scripts': [
            'tm-editor = tmEditor.__main__:main',
        ],
    },
    test_suite='tests',
    license="GPLv3",
)
