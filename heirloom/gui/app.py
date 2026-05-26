import sys
import os
from importlib import resources

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from .backend import CONFIG_FILE, GuiController


def main():
    os.environ.setdefault('QSG_RHI_BACKEND', 'opengl')
    reconfigure = '--reconfigure' in sys.argv
    qt_argv = [arg for arg in sys.argv if arg != '--reconfigure']

    QCoreApplication.setApplicationName('Heirloom Games Manager')
    QCoreApplication.setOrganizationName('HeirloomGM')

    if reconfigure and CONFIG_FILE.is_file():
        CONFIG_FILE.unlink()

    app = QGuiApplication(qt_argv)
    controller = GuiController()

    logo_path = resources.files('heirloom.gui') / 'assets' / 'heirloom.png'
    spinner_path = resources.files('heirloom.gui') / 'assets' / 'heirloom_spinner.png'
    if logo_path.is_file():
        app.setWindowIcon(QIcon(str(logo_path)))

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('controller', controller)
    engine.rootContext().setContextProperty('gamesModel', controller.filtered_games)
    engine.rootContext().setContextProperty('logoPath', QUrl.fromLocalFile(str(logo_path)).toString())
    engine.rootContext().setContextProperty('spinnerPath', QUrl.fromLocalFile(str(spinner_path)).toString())

    qml_path = resources.files('heirloom.gui') / 'qml' / 'Main.qml'
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 1

    controller.bootstrap()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
