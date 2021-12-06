import sys
from pathlib import Path

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox,
                             QDesktopWidget, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QPushButton, QRadioButton,
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


class Component(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._setLayout()
        self._createWidgets()

        self.setLayout(self.layout)

    def _setLayout(self) -> None:
        self.layout = QGridLayout()

    def _createWidgets(self) -> None:
        pass

    def _connectSlots(self, handler) -> None:
        pass

    def _wrapInGroupBox(self) -> None:
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

    def connectSlots(self, handler) -> None:
        self.commandCpn._connectSlots(handler)
        self.featureSelectorCpn._connectSlots(handler)
        self.featureOptionCpn._connectSlots(handler)

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

    def setValueToState(self, events: dict) -> None:
        for objectName, value in events.items():
            if objectName == 'dragDropFile':
                self.paths = value
            elif objectName == 'featureSelectorCbb':
                self.feature = self.metaKeys[value]
            elif objectName == 'copyAudioChk' or objectName == 'overwriteChk':
                self.generalParams[objectName] = value
            elif objectName == 'fromTimeTbx' or objectName == 'toTimeTbx':
                self.featureParams = {}
                self.featureParams[objectName] = value
            elif objectName == 'blankRectangle':
                self.featureParams = {}
                self.featureParams[objectName] = value
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

    def createCommand(self, events: dict) -> str:
        self.setValueToState(events)

        commandChain = ['ffmpeg']

        if self.forceFormat:
            commandChain.append(self.forceFormat)

        if self.paths and len(self.paths) > 0:
            inputPath = Path(self.paths[0]).__str__()
            commandChain.append('-i "{}"'.format(inputPath))

        if self.feature == 'FORMAT':
            pass
        elif self.feature == 'CUT':
            fromTime = self.featureParams.get('fromTimeTbx')
            if fromTime:
                commandChain.append('-ss {}'.format(fromTime))
            toTime = self.featureParams.get('toTimeTbx')
            if toTime:
                commandChain.append('-to {}'.format(toTime))
        elif self.feature == 'CONCAT':
            pass
        elif self.feature == 'RMBLBAR':
            blankRectangle = self.featureParams.get('blankRectangle') or ''
            commandChain.append('-vf crop={}'.format(blankRectangle))
        elif self.feature == 'ROTATE':
            rotateModeGroup = self.featureParams.get('rotateModeGroup') or ''
            commandChain.append('-vf transpose={}'.format(rotateModeGroup))
        elif self.feature == 'CROP':
            cropRectangle = self.featureParams.get('cropTbx') or ''
            commandChain.append('-vf crop={}'.format(cropRectangle))

        if self.generalParams.get('copyAudioChk'):
            commandChain.append('-c:a copy')
        if self.generalParams.get('overwriteChk'):
            commandChain.append('-y')

        if self.paths and len(self.paths) > 0:
            output = self.getOutput(self.paths[0], self.feature)
            commandChain.append('"{}"'.format(output.get('path')))

        return ' '.join(commandChain)

    def getBlankRectangle(self, input: str) -> str:
        pos1 = input.rfind('crop=') + 5
        pos2 = input.find('frame=', pos1)
        blankRectangle = input[pos1:pos2].rstrip()
        return blankRectangle


class Controller():
    def __init__(self, view: View, model: Model) -> None:
        self.view = view
        self.model = model

        self.view.connectSlots(self.handleEvents)
        self.view.addDragDropFileHandler(self.handleDragDropFile)

        self.process = None

        self.log = ''

        self.dialog = Dialog(self.view)
        self.dialog.setModal(True)
        self.dialog.connectSignals(self.handleDialogReject)

        self.setInitialStates()

    def setInitialStates(self) -> None:
        self.view.commandCpn.commandOptionCpn.copyAudioChk.setChecked(True)
        self.model.setValueToState({
            'copyAudioChk': True
        })

    def handleEvents(self, value) -> None:
        objectName = self.view.sender().objectName()

        if objectName == 'executeBtn':
            command = self.view.getCommand()
            self.executeCommand(command)
        elif objectName == 'cropBlankBtn':
            paths = self.model.paths
            if paths and len(paths) > 0:
                command = 'ffmpeg -i {} -ss 60 -vframes 10 -vf cropdetect -f null -'.format(
                    paths[0])
                # self.view.setCommand(command)
                self.executeCommand(command)
        else:
            if objectName == 'featureSelectorCbb':
                self.view.showFeatureOptions(list(META.keys())[value])

            command = self.model.createCommand({objectName: value})
            self.view.setCommand(command)

    def handleDragDropFile(self, paths) -> None:
        command = self.model.createCommand({'dragDropFile': paths})
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
        self.log += stdout

    def handleError(self) -> None:
        errorStream = self.process.readAllStandardError()
        stderr = bytes(errorStream).decode('utf8')
        self.log += stderr

    def handleStateChange(self, state) -> None:
        if state == QProcess.ProcessState.NotRunning:
            pass
        elif state == QProcess.ProcessState.Starting:
            self.log = ''
            self.dialog.show()
        elif state == QProcess.ProcessState.Running:
            pass

    def handleFinish(self) -> None:
        self.dialog.reject()
        self.process = None

        if self.model.feature == 'RMBLBAR':
            blankRectangle = self.model.getBlankRectangle(self.log)
            command = self.model.createCommand(
                {'blankRectangle': blankRectangle})
            self.view.setCommand(command)

    def handleDialogReject(self) -> None:
        self.dialog.reject()
        self.process.kill()
        self.process = None


class Dialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout()

        label = QLabel("FFmpeg command is executing")
        self.layout.addWidget(label)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

    def connectSignals(self, handler) -> None:
        self.buttonBox.rejected.connect(handler)


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
        self.executeBtn.setStyleSheet('font-size: 21px;')
        self.layout.addWidget(self.executeBtn, 0, 1)

        self.commandOptionCpn = CommandOptionComponent()
        self.layout.addWidget(self.commandOptionCpn, 1, 0)

    def _connectSlots(self, handler) -> None:
        self.commandTxb.textChanged.connect(handler)
        self.executeBtn.clicked.connect(handler)
        self.commandOptionCpn._connectSlots(handler)


class CommandOptionComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

    def _createWidgets(self) -> None:
        self.copyAudioChk = QCheckBox('Copy audio stream')
        self.copyAudioChk.setObjectName('copyAudioChk')
        self.layout.addWidget(self.copyAudioChk)

        self.overwriteChk = QCheckBox('Overwrite')
        self.overwriteChk.setObjectName('overwriteChk')
        self.layout.addWidget(self.overwriteChk)

        self.layout.addStretch()

    def _connectSlots(self, handler) -> None:
        self.copyAudioChk.toggled.connect(handler)
        self.overwriteChk.toggled.connect(handler)


class FeatureSelectorComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QVBoxLayout()

    def _createWidgets(self) -> None:
        self.featureSelectorCbb = QComboBox()
        self.featureSelectorCbb.setObjectName('featureSelectorCbb')
        self.featureSelectorCbb.setStyleSheet('font-size: 21px;')
        self.featureSelectorCbb.addItems(
            [META[key]["label"] for key in META])
        self.layout.addWidget(self.featureSelectorCbb)

        self.layout.addStretch()

    def _connectSlots(self, handler) -> None:
        self.featureSelectorCbb.activated[int].connect(handler)


class FeatureOptionComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

    def _createWidgets(self) -> None:
        self.cutFeatureOptionCpn = CutFeatureOptionComponent()
        self.layout.addWidget(self.cutFeatureOptionCpn)

        self.rmBlBarFeatureOptionCpn = RmBlBarFeatureOptionComponent()
        self.layout.addWidget(self.rmBlBarFeatureOptionCpn)

        self.cropFeatureOptionCpn = CropFeatureOptionComponent()
        self.layout.addWidget(self.cropFeatureOptionCpn)

        self.rotateFeatureOptionCpn = RotateFeatureOptionComponent()
        self.layout.addWidget(self.rotateFeatureOptionCpn)

        self.hideAllWidgets()

    def _connectSlots(self, handler) -> None:
        self.cutFeatureOptionCpn._connectSlots(handler)
        self.rmBlBarFeatureOptionCpn._connectSlots(handler)
        self.cropFeatureOptionCpn._connectSlots(handler)
        self.rotateFeatureOptionCpn._connectSlots(handler)

    def showFeatureOptions(self, feature) -> None:
        self.hideAllWidgets()
        if feature == 'CUT':
            self.cutFeatureOptionCpn.show()
        elif feature == 'RMBLBAR':
            self.rmBlBarFeatureOptionCpn.show()
        elif feature == 'CROP':
            self.cropFeatureOptionCpn.show()
        elif feature == 'ROTATE':
            self.rotateFeatureOptionCpn.show()

    def hideAllWidgets(self) -> None:
        self.cutFeatureOptionCpn.hide()
        self.rmBlBarFeatureOptionCpn.hide()
        self.cropFeatureOptionCpn.hide()
        self.rotateFeatureOptionCpn.hide()


class CutFeatureOptionComponent(Component):
    def _createWidgets(self) -> None:
        self.fromTimeTbx = QLineEdit()
        self.fromTimeTbx.setObjectName('fromTimeTbx')
        self.fromTimeTbx.setPlaceholderText('hh:mm:ss.ms')
        fromTimeSubLayout = QFormLayout()
        fromTimeSubLayout.addRow('From:', self.fromTimeTbx)
        self.layout.addLayout(fromTimeSubLayout, 0, 0)

        self.toTimeTbx = QLineEdit()
        self.toTimeTbx.setObjectName('toTimeTbx')
        self.toTimeTbx.setPlaceholderText('hh:mm:ss.ms')
        toTimeSubLayout = QFormLayout()
        toTimeSubLayout.addRow('To:', self.toTimeTbx)
        self.layout.addLayout(toTimeSubLayout, 0, 1)

    def _connectSlots(self, handler) -> None:
        self.fromTimeTbx.textChanged.connect(handler)
        self.toTimeTbx.textChanged.connect(handler)


class RmBlBarFeatureOptionComponent(Component):
    def _createWidgets(self) -> None:
        self.cropBlankBtn = QPushButton('Get blank bar rectangle')
        self.cropBlankBtn.setObjectName('cropBlankBtn')
        self.layout.addWidget(self.cropBlankBtn, 0, 0)

        label = QLabel('-->')
        self.layout.addWidget(label, 0, 1)

        self.cropBlankTbx = QLineEdit()
        self.cropBlankTbx.setReadOnly(True)
        self.layout.addWidget(self.cropBlankTbx, 0, 2)

    def _connectSlots(self, handler) -> None:
        self.cropBlankBtn.clicked.connect(handler)


class CropFeatureOptionComponent(Component):
    def _setLayout(self) -> None:
        self.layout = QFormLayout()

    def _createWidgets(self) -> None:
        self.cropTbx = QLineEdit()
        self.cropTbx.setObjectName('cropTbx')
        self.cropTbx.setPlaceholderText('w:h:x:y')
        self.layout.addRow('Crop:', self.cropTbx)

    def _connectSlots(self, handler) -> None:
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

    def _connectSlots(self, handler) -> None:
        self.rotateModeGroup.idToggled.connect(handler)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = View()
    model = Model()
    controller = Controller(view, model)
    view.show()
    sys.exit(app.exec_())
