# -*- mode: python ; coding: utf-8 -*-


from pathlib import Path
import platform
import os

_ROOT = Path(os.getcwd()).resolve()
_ASSETS = _ROOT / 'assets'
_ICON_PNG = _ASSETS / 'logo.png'
_ICON_ICNS = _ASSETS / 'logo.icns'
_ICON_ICO = _ASSETS / 'logo.ico'

def _pick_icon() -> str | None:
    try:
        if platform.system() == 'Darwin' and _ICON_ICNS.exists():
            return str(_ICON_ICNS)
        if platform.system() == 'Windows' and _ICON_ICO.exists():
            return str(_ICON_ICO)
        if _ICON_PNG.exists():
            return str(_ICON_PNG)
    except Exception:
        pass
    return None

_ICON_PATH = _pick_icon()

_datas = []
if (_ASSETS / 'logo.png').exists():
    _datas.append((str(_ASSETS / 'logo.png'), 'assets'))
if (_ASSETS / 'profile.jpeg').exists():
    _datas.append((str(_ASSETS / 'profile.jpeg'), 'assets'))
if (_ASSETS / 'icons').exists():
    _datas.append((str(_ASSETS / 'icons'), 'assets/icons'))

a = Analysis(
    [str(_ROOT / 'desktop_app.py')],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AskDB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_ICON_PATH,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AskDB',
)
app = BUNDLE(
    coll,
    name='AskDB.app',
    icon=_ICON_PATH,
    bundle_identifier=None,
)
