import sys
from pathlib import Path

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox,
                             QDesktopWidget, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QProgressDialog, QPushButton, QRadioButton,
                             QVBoxLayout, QWidget)

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

        self.centralWidget = DragDropFileWidget(self)
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

    def addDragDropFileHandler(self, handler) -> None:
        self.centralWidget._addDragDropFileHandler(handler)

    def setCommand(self, command) -> None:
        self.commandCpn.commandTxb.setText(command)

    def getCommand(self) -> str:
        return self.commandCpn.commandTxb.text()

    def showFeatureOptions(self, feature) -> None:
        self.featureOptionCpn.showFeatureOptions(feature)


class Model():
    def __init__(self) -> None:
        self.metaKeys = list(META.keys())
        self.paths = []
        self.feature = self.metaKeys[0]
        self.generalParams = {}
        self.featureParams = {}
        self.forceFormat = ''

    def setValueToState(self, objectName, value) -> None:
        if objectName == 'dragDropFile':
            self.paths = value
        elif objectName == 'featureSelectorCbb':
            self.feature = self.metaKeys[value]
        elif objectName == 'copyAudioChk' or objectName == 'overwriteChk':
            self.generalParams[objectName] = value
        elif objectName == 'cropTbx':
            self.featureParams = {}
            self.featureParams[objectName] = value
        elif objectName == 'rotateModeGroup':
            self.featureParams = {}
            self.featureParams[objectName] = value

    def getOutput(self, inputPath, suffix) -> dict:
        inputFileName = Path(inputPath).stem
        directory = Path(inputPath).parent
        outputFileName = '{}_{}.mp4'.format(inputFileName, suffix)
        outputFilePath = Path(directory).joinpath(outputFileName).__str__()
        return {'name': outputFileName, 'path': outputFilePath}

    def createCommand(self, objectName, value) -> str:
        self.setValueToState(objectName, value)

        commandChain = ['ffmpeg']

        if self.forceFormat:
            commandChain.append(self.forceFormat)

        if self.paths and len(self.paths) > 0:
            inputPath = Path(self.paths[0]).__str__()
            commandChain.append('-i "{}"'.format(inputPath))

        if self.feature == 'FORMAT':
            pass
        elif self.feature == 'CUT':
            pass
        elif self.feature == 'CONCAT':
            pass
        elif self.feature == 'RMBLBAR':
            pass
        elif self.feature == 'ROTATE':
            rotateModeGroup = self.featureParams.get('rotateModeGroup') or ''
            commandChain.append('-vf transpose={}'.format(rotateModeGroup))
        elif self.feature == 'CROP':
            cropTbx = self.featureParams.get('cropTbx') or ''
            commandChain.append('-vf crop={}'.format(cropTbx))

        if self.generalParams.get('copyAudioChk'):
            commandChain.append('-c:a copy')
        if self.generalParams.get('overwriteChk'):
            commandChain.append('-y')

        if self.paths and len(self.paths) > 0:
            output = self.getOutput(self.paths[0], self.feature)
            commandChain.append('"{}"'.format(output.get('path')))

        return ' '.join(commandChain)


class Controller():
    def __init__(self, view: View, model: Model) -> None:
        self.view = view
        self.model = model

        self.view.connectSignals(self.handleEvents)
        self.view.addDragDropFileHandler(self.handleDragDropFile)

        self.process = None
        self.dialog = None

    def handleEvents(self, value) -> None:
        objectName = self.view.sender().objectName()

        if objectName == 'executeBtn':
            command = self.view.getCommand()
            self.executeCommand(command)
        else:
            if objectName == 'featureSelectorCbb':
                self.view.showFeatureOptions(list(META.keys())[value])

            command = self.model.createCommand(objectName, value)
            self.view.setCommand(command)

    def handleDragDropFile(self, paths) -> None:
        command = self.model.createCommand('dragDropFile', paths)
        self.view.setCommand(command)

    def executeCommand(self, command: str) -> None:
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handleOutput)
        self.process.readyReadStandardError.connect(self.handleError)
        self.process.stateChanged.connect(self.handleStateChange)
        self.process.finished.connect(self.handleFinish)
        if command.startswith('ffmpeg'):
            self.process.start(command)

    def handleOutput(self) -> None:
        outputStream = self.process.readAllStandardOutput()
        stdout = bytes(outputStream).decode('utf8')
        print(stdout)

    def handleError(self) -> None:
        errorStream = self.process.readAllStandardError()
        stderr = bytes(errorStream).decode('utf8')
        print(stderr)

    def handleStateChange(self, state) -> None:
        if state == QProcess.ProcessState.NotRunning:
            pass
        elif state == QProcess.ProcessState.Starting:
            self.dialog = QProgressDialog(self.view)
            self.dialog.setMinimum(0)
            self.dialog.setMaximum(100)
            self.dialog.setModal(True)
            self.dialog.show()
        elif state == QProcess.ProcessState.Running:
            pass

    def handleFinish(self) -> None:
        self.dialog.cancel()
        print("Finish")
        self.process = None


class DragDropFileWidget(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self.setAcceptDrops(True)
        self.paths = []
        self.handler = None

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            self.paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.paths.append(str(url.toLocalFile()))
                else:
                    self.paths.append(str(url.toString()))

            if self.handler:
                self.handler(self.paths)
        else:
            event.ignore()

    def _addDragDropFileHandler(self, handler) -> None:
        self.handler = handler


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
        self.cropFeatureOptionWrapper = QWidget()
        self.cropFeatureOptionWrapper.setLayout(
            self.cropFeatureOptionCpn.layout)
        self.layout.addWidget(self.cropFeatureOptionWrapper, 0, 0)

        self.rotateFeatureOptionCpn = RotateFeatureOptionComponent()
        self.rotateFeatureOptionWrapper = QWidget()
        self.rotateFeatureOptionWrapper.setLayout(
            self.rotateFeatureOptionCpn.layout)
        self.layout.addWidget(self.rotateFeatureOptionWrapper, 1, 0)

        self.hideAllWidgets()

    def _connectSignals(self, handler) -> None:
        self.cropFeatureOptionCpn._connectSignals(handler)
        self.rotateFeatureOptionCpn._connectSignals(handler)

    def showFeatureOptions(self, feature) -> None:
        self.hideAllWidgets()
        if feature == 'CROP':
            self.cropFeatureOptionWrapper.show()
        elif feature == 'ROTATE':
            self.rotateFeatureOptionWrapper.show()

    def hideAllWidgets(self) -> None:
        self.cropFeatureOptionWrapper.hide()
        self.rotateFeatureOptionWrapper.hide()


class CropFeatureOptionComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QFormLayout()

    def _createWidgets(self) -> None:
        self.cropTbx = QLineEdit()
        self.cropTbx.setObjectName('cropTbx')
        self.cropTbx.setPlaceholderText('w:h:x:y')
        self.layout.addRow('Crop:', self.cropTbx)

    def _connectSignals(self, handler) -> None:
        self.cropTbx.textChanged.connect(handler)


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
        self.rotateModeGroup.idToggled.connect(handler)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = View()
    model = Model()
    controller = Controller(view, model)
    view.show()
    sys.exit(app.exec_())
