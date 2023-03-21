Trigger Menu Editor
===================

## Install

Install using pip (>= 19.0)

```bash
pip install --upgrade pip
pip install git+https://github.com/cms-l1-globaltrigger/tm-editor.git@0.15.0
```

## Build

Regenerate the PyQt5 resource module.

```bash
pyrcc5 resource/tmEditor.rcc -o tmEditor/tmeditor_rc.py
```

## Synopsis

    $ tm-editor <filename|URL ...>

## Example

Opening a local XML file:

    $ tm-editor L1Menu_Sample.xml

Opening a remote XML resource:

    $ tm-editor http://example.com/L1Menu_Sample.xml
