Building documentation
======================

## Requirements

On RedHat based distributions:

    sudo yum install python-pip
    sudo pip install sphinx sphinx-rtd-theme

On Debian based distributions:

    sudo apt-get install python-pip
    sudo pip install sphinx sphinx-rtd-theme

## Building HTML documentation

    make html

The generated documentation can be accessed at

   _build/html/index.html
