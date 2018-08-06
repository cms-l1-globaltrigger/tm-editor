Trigger Menu Editor
===================

## Dependecies

 * PyQt5 (PyQt4 as fallback)
 * utm (>= 0.6.5)
   * xerces-c
   * boost-system, boost-filesystem
   * tmGrammar, tmTable, tmXsd, tmUtil

## Build locally

    $ source path/to/utm/setup.sh
    $ make

**Note:** running the makefile is required to build the resource python module.

## Synopsis

    $ tm-editor <filename|URL ...>

## Example

Opening a local XML file:

    $ tm-editor L1Menu_Sample.xml

Opening a remote XML resource:

    $ tm-editor http://example.com/L1Menu_Sample.xml
