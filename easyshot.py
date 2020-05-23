import sys

from PyQt5.QtWidgets import QApplication
from screen_capture import CaptureScreen

if __name__ == '__main__':
    app = QApplication(sys.argv)
    cs = CaptureScreen()
    cs.setWindowTitle('EasyScreenShot')
    cs.show()
    sys.exit(app.exec_())
