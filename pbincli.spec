# -*- mode: python -*-

from pkg_resources import parse_version
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct
from pbincli.__init__ import __version__ as pbincli_version, __copyright__ as pbincli_copyright

pbincli_ver = parse_version(pbincli_version)

block_cipher = None

a = Analysis(['pbincli\\cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
    cipher=block_cipher)
exe = EXE(pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pbincli-' + pbincli_version,
    version=VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=(pbincli_ver.major, pbincli_ver.minor, pbincli_ver.micro, 0),
            prodvers=(pbincli_ver.major, pbincli_ver.minor, pbincli_ver.micro, 0),
            mask=0x3f,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0)
        ),
        kids=[
            StringFileInfo([
                StringTable(
                    u'040904B0',
                    [
                        StringStruct(u'FileDescription', u'PrivateBin CLI'),
                        StringStruct(u'FileVersion', pbincli_version),
                        StringStruct(u'InternalName', u'pbincli'),
                        StringStruct(u'LegalCopyright', pbincli_copyright),
                        StringStruct(u'OriginalFilename', u'pbincli-' + pbincli_version + u'.exe'),
                        StringStruct(u'ProductName', u'PBinCLI'),
                        StringStruct(u'ProductVersion', pbincli_version)
                    ]
                )
            ]),
            VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
        ]
    ),
    icon=['contrib\\privatebin.ico'],
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=True)
