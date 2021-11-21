from PyQt5.QtWidgets import QApplication, QButtonGroup, QCheckBox, QComboBox, QDesktopWidget, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout, QLayoutItem, QLineEdit, QMainWindow, QPushButton, QRadioButton, QVBoxLayout, QWidget
import sys


META = {
    "FORMAT": {
        "label": "Format",
    },
    "CUT": {
        "label": "Cut",
    },
    "CONCAT": {
        "label": "Concatenate",
    },
    "RMBLBAR": {
        "label": "Remove blank bar",
    },
    "ROTATE": {
        "label": "Rotate",
    },
    "CROP": {
        "label": "Crop",
    },
}

ROTATE_MODE = (
    {
        "value": 1,
        "label": "Rotate 90deg",
    },
    {
        "value": 2,
        "label": "Rotate -90deg",
    },
    {
        "value": 3,
        "label": "Rotate 90deg and flip vertically",
    },
    {
        "value": 4,
        "label": "Rotate -90deg and flip vertically",
    },
)


class Component():
    def __init__(self) -> None:
        super().__init__()
        self.layout = None
        self._setLayout()
        self._createWidgets()

    def _setLayout(self) -> None:
        self.layout = QGridLayout()

    def _createWidgets(self) -> None:
        pass

    def _connectSignals(self, handler) -> None:
        pass

    def _wrapInGroupBox(self) -> QGroupBox:
        groupBox = QGroupBox()
        groupBox.setLayout(self.layout)
        return groupBox


class View(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle('Video editor')

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        screen = QDesktopWidget().screenGeometry()
        self.move(screen.width() // 2, screen.height() // 2)

        self.createWidgets()

    def createWidgets(self) -> None:
        layout = QGridLayout()

        self.commandCpn = CommandComponent()
        layout.addWidget(self.commandCpn._wrapInGroupBox(), 0, 0, 1, 3)

        self.featureSelectorCpn = FeatureSelectorComponent()
        layout.addWidget(self.featureSelectorCpn._wrapInGroupBox(), 1, 0)

        self.featureOptionCpn = FeatureOptionComponent()
        layout.addWidget(self.featureOptionCpn._wrapInGroupBox(), 1, 1, 1, 2)

        self.centralWidget.setLayout(layout)

    def connectSignals(self, handler) -> None:
        self.commandCpn._connectSignals(handler)
        self.featureSelectorCpn._connectSignals(handler)
        self.featureOptionCpn._connectSignals(handler)

    def setCommand(self, command) -> None:
        self.commandCpn.commandTxb.setText(command)


class Model():
    def __init__(self) -> None:
        pass

    def makeACommand(self, objectName, value) -> str:
        return 'aaa'


class Controller():
    def __init__(self, view: View, model: Model) -> None:
        self.view = view
        self.model = model

        self.view.connectSignals(self.handleEvents)

    def handleEvents(self, value) -> None:
        objectName = self.view.sender().objectName()
        command = self.model.makeACommand(objectName, value)
        self.view.setCommand(command)


class CommandComponent(Component):
    def _createWidgets(self) -> None:
        self.commandTxb = QLineEdit()
        self.commandTxb.setObjectName('commandTbx')
        self.commandTxb.setPlaceholderText('Type FFmpeg command')
        self.commandTxb.setStyleSheet('padding: 5px; width: 43em;')
        self.layout.addWidget(self.commandTxb, 0, 0)

        self.executeBtn = QPushButton('Execute')
        self.executeBtn.setObjectName('executeBtn')
        self.executeBtn.setStyleSheet('font-size: 18px;')
        self.layout.addWidget(self.executeBtn, 0, 1)

        self.commandOptionCpn = CommandOptionComponent()
        self.layout.addLayout(self.commandOptionCpn.layout, 1, 0)

    def _connectSignals(self, handler) -> None:
        self.commandTxb.textChanged.connect(handler)
        self.executeBtn.clicked.connect(handler)
        self.commandOptionCpn._connectSignals(handler)


class CommandOptionComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QHBoxLayout()

    def _createWidgets(self) -> None:
        self.copyAudioChk = QCheckBox('Copy audio stream')
        self.copyAudioChk.setObjectName('copyAudioChk')
        self.layout.addWidget(self.copyAudioChk)

        self.overwriteChk = QCheckBox('Overwrite')
        self.overwriteChk.setObjectName('overwriteChk')
        self.layout.addWidget(self.overwriteChk)

        self.layout.addStretch()

    def _connectSignals(self, handler) -> None:
        self.copyAudioChk.toggled.connect(handler)
        self.overwriteChk.toggled.connect(handler)


class FeatureSelectorComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QVBoxLayout()

    def _createWidgets(self) -> None:
        self.featureSelectorCbb = QComboBox()
        self.featureSelectorCbb.setObjectName('featureSelectorCbb')
        self.featureSelectorCbb.setStyleSheet('font-size: 15px;')
        self.featureSelectorCbb.addItems(
            [META[key]["label"] for key in META])
        self.layout.addWidget(self.featureSelectorCbb)

        self.layout.addStretch()

    def _connectSignals(self, handler) -> None:
        self.featureSelectorCbb.activated[int].connect(handler)


class FeatureOptionComponent(Component):
    def _createWidgets(self) -> None:
        self.cropFeatureOptionCpn = CropFeatureOptionComponent()
        self.layout.addLayout(self.cropFeatureOptionCpn.layout, 0, 0)

        self.rotateFeatureOptionCpn = RotateFeatureOptionComponent()
        self.layout.addLayout(self.rotateFeatureOptionCpn.layout, 1, 0)

    def _connectSignals(self, handler) -> None:
        self.cropFeatureOptionCpn._connectSignals(handler)
        self.rotateFeatureOptionCpn._connectSignals(handler)


class CropFeatureOptionComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QFormLayout()

    def _createWidgets(self) -> None:
        self.cropTxb = QLineEdit()
        self.cropTxb.setObjectName('cropTxb')
        self.cropTxb.setPlaceholderText('w:h:x:y')
        self.layout.addRow('Crop:', self.cropTxb)

    def _connectSignals(self, handler) -> None:
        self.cropTxb.textChanged.connect(handler)


class RotateFeatureOptionComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QFormLayout()

    def _createWidgets(self) -> None:
        self.rotateModeGroup = QButtonGroup()
        self.rotateModeGroup.setObjectName('rotateModeGroup')
        rotateModeLayout = QVBoxLayout()
        for mode in ROTATE_MODE:
            rotateModeRdo = QRadioButton(mode['label'])
            rotateModeLayout.addWidget(rotateModeRdo)
            self.rotateModeGroup.addButton(rotateModeRdo, mode['value'])

        self.layout.addRow('Rotate mode:', rotateModeLayout)

    def _connectSignals(self, handler) -> None:
        self.rotateModeGroup.buttonToggled.connect(handler)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = View()
    model = Model()
    controller = Controller(view, model)
    view.show()
    sys.exit(app.exec_())
