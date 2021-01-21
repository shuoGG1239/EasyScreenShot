import win32api
import win32clipboard
import win32con

from PyQt5.QtCore import Qt, qAbs, QRect, QByteArray, QBuffer, QIODevice
from PyQt5.QtGui import QGuiApplication, QColor, QPen, QPainter
from PyQt5.QtWidgets import QWidget, QApplication

# 0:保存图片到桌面 1:复制到剪贴板 2:保存图片并复制到剪贴板
RUN_MODE = 2


# 暂时仅支持windows
class CaptureScreen(QWidget):
    """
    截屏: 使用时仅需直接new一个该实例即可出现全屏的截屏界面
    """
    load_pixmap = None
    screen_width = None
    screen_height = None
    is_mouse_pressed = None
    begin_pos = None
    end_pos = None
    capture_pixmap = None
    painter = QPainter()

    def __init__(self):
        QWidget.__init__(self)
        self.init_window()
        self.load_background_pixmap()
        self.setCursor(Qt.CrossCursor)
        self.show()

    def init_window(self):
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowActive | Qt.WindowFullScreen)

    def load_background_pixmap(self):
        # 截下当前屏幕的图像
        self.load_pixmap = QGuiApplication.primaryScreen().grabWindow(QApplication.desktop().winId())
        self.screen_width = self.load_pixmap.width()
        self.screen_height = self.load_pixmap.height()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_mouse_pressed = True
            self.begin_pos = event.pos()
        if event.button() == Qt.RightButton:
            self.close()
        return QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.is_mouse_pressed is True:
            self.end_pos = event.pos()
            self.update()
        return QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.end_pos = event.pos()
        self.is_mouse_pressed = False
        return QWidget.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        if self.capture_pixmap is not None:
            self.handle_image(self.capture_pixmap)
            self.close()

    def paintEvent(self, event):
        self.painter.begin(self)
        shadow_color = QColor(0, 0, 0, 100)  # 阴影颜色设置
        self.painter.setPen(QPen(Qt.blue, 1, Qt.SolidLine, Qt.FlatCap))  # 设置画笔
        self.painter.drawPixmap(0, 0, self.load_pixmap)  # 将背景图片画到窗体上
        self.painter.fillRect(self.load_pixmap.rect(), shadow_color)  # 画影罩效果
        if self.is_mouse_pressed:
            selected_rect = self.get_rect(self.begin_pos, self.end_pos)
            self.capture_pixmap = self.load_pixmap.copy(selected_rect)
            self.painter.drawPixmap(selected_rect.topLeft(), self.capture_pixmap)
            self.painter.drawRect(selected_rect)
        self.painter.end()  # 重绘结束

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_image(self.capture_pixmap)
            self.close()

    def get_rect(self, beginPoint, endPoint):
        width = qAbs(beginPoint.x() - endPoint.x())
        height = qAbs(beginPoint.y() - endPoint.y())
        x = beginPoint.x() if beginPoint.x() < endPoint.x() else endPoint.x()
        y = beginPoint.y() if beginPoint.y() < endPoint.y() else endPoint.y()
        selected_rect = QRect(x, y, width, height)
        # 避免宽或高为零时拷贝截图有误
        # 可以看QQ截图，当选取截图宽或高为零时默认为2
        if selected_rect.width() == 0:
            selected_rect.setWidth(1)
        if selected_rect.height() == 0:
            selected_rect.setHeight(1)
        return selected_rect

    def handle_image(self, pixmap):
        if RUN_MODE == 0:
            self.save_image(pixmap)
        if RUN_MODE == 1:
            self.paste_on_clipboard(pixmap)
        if RUN_MODE == 2:
            self.save_image(pixmap)
            self.paste_on_clipboard(pixmap)

    def save_image(self, pixmap):
        import os
        import datetime
        now_time = datetime.datetime.now()
        now_time_str = now_time.strftime("%Y%m%d%H%M%S")
        p = os.path.join(self.get_desktop_path(), "easyscreenshot" + now_time_str + '.jpg')
        pixmap.save(p, 'jpg')

    def get_desktop_path(self):
        key = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER,
                                  r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders', 0,
                                  win32con.KEY_READ)
        return win32api.RegQueryValueEx(key, 'Desktop')[0]

    def paste_on_clipboard(self, pixmap):
        ba = QByteArray()
        buff = QBuffer(ba)
        buff.open(QIODevice.WriteOnly)
        pixmap.save(buff, "bmp")
        pixmap_bytes = ba.data()
        self.set_clipboard_img(pixmap_bytes)
        print(len(pixmap_bytes))

    def set_clipboard_img(self, img_bytes):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        # BMP前14位为header,须截掉否则很多软件识别不出
        win32clipboard.SetClipboardData(win32con.CF_DIB, img_bytes[14:])
        win32clipboard.CloseClipboard()
