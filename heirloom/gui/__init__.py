import platform
import sys
from importlib import metadata


def _diagnose():
    def version(package):
        try:
            return metadata.version(package)
        except metadata.PackageNotFoundError:
            return 'not installed'

    print('Heirloom GUI diagnostics')
    print(f'Python: {sys.version.split()[0]}')
    print(f'Executable: {sys.executable}')
    print(f'Platform: {platform.platform()}')
    print(f'Machine: {platform.machine()}')
    print(f'Processor: {platform.processor() or "unknown"}')
    print(f'heirloom: {version("heirloom")}')
    print(f'PySide6: {version("PySide6")}')
    print(f'PySide6-Qt6: {version("PySide6-Qt6")}')
    print(f'shiboken6: {version("shiboken6")}')


def main():
    if any(arg in ('--diagnose', '--diagnostics') for arg in sys.argv[1:]):
        _diagnose()
        return 0

    from .app import main as app_main

    return app_main()


__all__ = ['main']
