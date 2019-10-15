Trigger Menu Editor
===================

## Synopsis

    $ tm-editor <filename|URL ...>

## Example

Opening a local XML file:

    $ tm-editor L1Menu_Sample.xml

Opening a remote XML resource:

    $ tm-editor http://example.com/L1Menu_Sample.xml

## Dependencies

Install following utm wheels or build utm python bindings.

 * [`tm-eventsetup>=0.7.3`](https://github.com/cms-l1-globaltrigger/tm-eventsetup)
 * [`tm-grammar>=0.7.3`](https://github.com/cms-l1-globaltrigger/tm-grammar)
 * [`tm-table>=0.7.3`](https://github.com/cms-l1-globaltrigger/tm-table)

## Install

Install using pip

```bash
pip install git+https://github.com/cms-l1-globaltrigger/tm-editor.git@0.10.0
```
