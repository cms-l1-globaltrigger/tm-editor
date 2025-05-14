# Trigger Menu Editor

CMS Level-1 Trigger Menu Editor

## Install

Install using pip

```bash
pip install https://github.com/cms-l1-globaltrigger/tm-editor/archive/refs/tags/0.18.0.zip
```

## Build

Regenerate the PyQt5 resource module.

```bash
pyrcc5 resource/tmEditor.rcc -o tmEditor/tmeditor_rc.py
```

## Synopsis

```
tm-editor <filename|URL ...>
```

## Example

Opening a local XML file:

```bash
tm-editor L1Menu_Sample.xml
```

Opening a remote XML resource:

```bash
tm-editor http://example.com/L1Menu_Sample.xml
```
