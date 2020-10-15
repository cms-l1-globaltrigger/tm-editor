# -*- mode: python -*-
import os

entry_point = '_macos_app.py'
with open(entry_point, 'w') as f:
    f.write("from tmEditor.main import main; main()")

data_files = [
]

block_cipher = None

a = Analysis(
    [entry_point],
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=['tmGrammar', 'tmTable', 'tmEventSetup', 'markdown', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.sip'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='tm-editor',
    debug=False,
    strip=False,
    upx=True,
    console=False
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='tm-editor'
)
app = BUNDLE(
    coll,
    name='tm-editor.app',
    icon='tm-editor.icns',
    info_plist={
        'NSHighResolutionCapable': 'True'
    },
    bundle_identifier=None
)

