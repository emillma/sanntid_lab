import sys
from PyQt5 import QtGui, QtWidgets
import qdarkstyle
from mainwindow import Ui_MainWindow


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        self.version = '1.0'

        QtWidgets.QMainWindow.__init__(self)

        Ui_MainWindow.__init__(self)
        self.setupUi(self)

    def set_text(self, text):
        self.label.setText(text)



def run():
    # print(__file__)
    # logger.info('hello there')
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    # app.setWindowIcon(QtGui.QIcon(':icons/icon.png'))
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    window = MyApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()