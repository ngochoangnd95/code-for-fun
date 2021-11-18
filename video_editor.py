from PyQt5.QtWidgets import QApplication, QDesktopWidget, QGridLayout, QMainWindow, QWidget
import sys


class Component():
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.layout = None
        self._setLayout()
        self._createWidgets()
    
    def _setLayout(self) -> None:
        self.layout = QGridLayout(self)
    
    def _createWidgets(self) -> None:
        pass


class View(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle('Video editor')

        self._centralWidget = Component(self)
        self.setCentralWidget(self._centralWidget)

        screen = QDesktopWidget().screenGeometry()
        self.move(screen.width() // 2, screen.height() // 2)


class Controller():
    def __init__(self, view, model) -> None:
        self.view = view
        self.model = model

        self._connectSignals()
    
    def _connectSignals(self) -> None:
        pass


class Model():
    def __init__(self) -> None:
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = View()
    model = Model()
    controller = Controller(view, model)
    view.show()
    sys.exit(app.exec_())
