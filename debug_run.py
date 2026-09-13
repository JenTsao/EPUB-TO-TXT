import sys

print("1: 开始导入", flush=True)
from PySide6.QtWidgets import QApplication

print("2: QtWidgets 导入成功", flush=True)
import main

print("3: main 模块导入成功", flush=True)
from ui.settings import SettingsManager, ThemeManager

app = QApplication(sys.argv)
print("4: QApplication 创建成功", flush=True)
ThemeManager.apply(app, "light")
print("5: 主题应用成功", flush=True)
w = main.MainWindow(SettingsManager())
print("6: 主窗口构造成功", flush=True)
w.show()
print("7: 窗口已 show", flush=True)
print(f"8: isVisible={w.isVisible()} winId={w.winId()}", flush=True)

from PySide6.QtCore import QTimer

QTimer.singleShot(3000, app.quit)
app.exec()
print("9: 事件循环退出", flush=True)
