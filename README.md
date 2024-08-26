Trigger Menu Editor
===================

## Install

Install using pip

```bash
pip install --extra-index-url https://globaltrigger.web.cern.ch/pypi/ tm-editor
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
