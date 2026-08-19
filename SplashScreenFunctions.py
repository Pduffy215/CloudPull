import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from Config import PROJECT_ROOT

ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')  # put your images in an 'assets' folder next to the script

class SplashFunctions(QMainWindow):
    def __init__(self):
        super().__init__()
        self.defineSplashGraphics()

    def defineSplashGraphics(self):
        self.pixmap = QPixmap(os.path.join(ASSETS_DIR, 'VStreamlogo.png'))
        self.pixmap2 = QPixmap(os.path.join(ASSETS_DIR, 'new logo blues smaller.png'))

        if self.pixmap.isNull():
            print(f"Warning: failed to load {os.path.join(ASSETS_DIR, 'VStreamlogo.png')}")
        if self.pixmap2.isNull():
            print(f"Warning: failed to load {os.path.join(ASSETS_DIR, 'new logo blues smaller.png')}")

        self.MainLogoLBL = QLabel()
        self.MainLogoLBL.setPixmap(self.pixmap)
        self.MainLogoLBL.setAlignment(Qt.AlignCenter)

        self.SplashLogoLBL = QLabel()
        self.SplashLogoLBL.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.SplashLogoLBL.setPixmap(self.pixmap2)

        # the QGridLayout controls their geometry once added below

        self.resize(self.pixmap.width() + 700, self.pixmap.height() + 700)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center() - self.rect().center())

        self.MainWidget = QWidget()
        self.MainLayout = QGridLayout()
        self.MainWidget.setLayout(self.MainLayout)

        self.MainLayout.addWidget(self.SplashLogoLBL, 0, 1, Qt.AlignTop | Qt.AlignRight)
        self.MainLayout.addWidget(self.MainLogoLBL, 1, 0, 1, 2, Qt.AlignCenter)
        self.MainLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 0, 0)
        self.MainLayout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 2, 0, 1, 2)

        self.setCentralWidget(self.MainWidget)


    def start_fade_in(self):
        self.effect = QGraphicsOpacityEffect(self.MainWidget)
        self.MainWidget.setGraphicsEffect(self.effect)

        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(2000)  # 2 seconds
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

        # hardcoded timer value that has to be kept in sync manually.
        # (1000 ms = however long you want the splash to hold at full opacity)
        self.animation.finished.connect(lambda: QTimer.singleShot(1000, self.start_fade_out))
        self.animation.start()


    def start_fade_out(self):
        self.animation2 = QPropertyAnimation(self.effect, b"opacity")  # reuse self.effect
        self.animation2.setDuration(2000)  # 2 seconds
        self.animation2.setStartValue(1)
        self.animation2.setEndValue(0)
        self.animation2.setEasingCurve(QEasingCurve.InOutCubic)

        self.animation2.finished.connect(self.close)

        self.animation2.start()
    #End Splash Screen Functions
