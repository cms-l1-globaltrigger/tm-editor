# -*- mode: python -*-
import os
from glob import glob

UTM_BASE = os.environ.get('UTM_BASE')
if not UTM_BASE:
    raise RuntimeError("UTM_BASE path not set")

data_files = [
    ('../tmXsd/*.xsd', 'xsd/.'),
    ('../tmXsd/xsd-type/*.xsd', 'xsd/xsd-type/.'),
]

block_cipher = None

a = Analysis(
    ['scripts/tm-editor'],
    pathex=[os.path.join(os.path.abspath(UTM_BASE), 'tmEditor')],
    binaries=[],
    datas=data_files,
    hiddenimports=[],
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
