'''
this setup uses an adaptation to the stytra package  to run behavioral experiments:

https://github.com/portugueslab/stytra

'''
import zmq
import time
import qdarkstyle
import sys

import numpy as np
import pygetwindow as gw
import threading as tr

from pathlib import Path

# GUI imports
from stytra.stimulation.stimuli import Stimulus
from stytra.experiments.tracking_experiments import TrackingExperiment
from stytra.gui.container_windows import TrackingExperimentWindow
from stytra.gui.camera_display import CameraViewWidget
from stytra.gui.buttons import IconButton
from stytra.gui.multiscope import MultiStreamPlot
from stytra import Protocol

from lightparam.gui import ControlCombo

from PyQt5.QtWidgets import QToolButton, QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import  QIcon
from PyQt5.QtCore import QSize


class TimeUpdater(Stimulus):
    """
    uses the stimulus framework from stytra to update timing externally
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # sends a signal out -- linked to the play button
        self.external_starter = 0
        self.go = None

        # This takes in timing information from external protocol
        self.timing = None
        # initializes with some bogus duration as a buffer
        self.duration = 300

        # initializes the variables to measure the time
        self.sent_times = [0, 0]
        self.exp_max = 99999999
        self.exp_elapsed = 0

        # this iterator makes it so we don't update every loop, only every so many loops
        self.iterator = 0
        self.timing_offset = 0
        self.fixed_duration = False

    # connects to stytra to get the internal experiment parameters from stytra
    def initialise_external(self, experiment):
        super().initialise_external(experiment)
        print()
        try:
            stims_socket = self._experiment.go_socket
            sending_context = zmq.Context()
            self.go = sending_context.socket(zmq.REQ)
            self.go.connect('tcp://localhost:' + str(stims_socket))
        except AttributeError:
            pass

        try:
            time_socket = self._experiment.timing_socket
            context = zmq.Context()
            self.timing = context.socket(zmq.SUB)
            self.timing.setsockopt(zmq.SUBSCRIBE, b'time')
            self.timing.connect(str("tcp://localhost:") + str(time_socket))
        except AttributeError:
            pass

    def update(self):

        # if condition met, update duration
        if self.external_starter == 0:
            self.go.send_string('True')
            self.external_starter = 1

        try:
            # check for a message, this will not block
            times_t = self.timing.recv_string(flags=zmq.NOBLOCK)
            self.sent_times = self.timing.recv_pyobj(flags=zmq.NOBLOCK)
            self.exp_max = self.sent_times[0]
            self.exp_elapsed = self.sent_times[1]

            if not self.fixed_duration:
                self.duration = np.float64(self.exp_max)
                self.fixed_duration = True

        except zmq.Again:
            pass

        # only update every 50 loop runs, this runs at ~30-40 Hz, hurts performance to do more often
        self.iterator += 1
        if self.iterator > 50:
            time_correction = self._elapsed - self.exp_elapsed - self.timing_offset

            if time_correction <= 0:
                time_correction = 0
            self.duration += time_correction
            self.timing_offset += time_correction
            self.iterator = 0


class StytraDummy(Protocol):
    """
    generic blank Stytra Protocol
    """
    name = "dummy"

    def __init__(self,):
        super().__init__()

    def get_stim_sequence(self):
        return [TimeUpdater()]


class LocalIconButton(QToolButton):
    def __init__(self, icon_name="", action_name="", size=[48, 32],*args, **kwargs):
        super().__init__(*args, **kwargs)

        prePath = Path(sys.executable).parents[0].joinpath(r'Lib\site-packages\pandastim\resources')

        self.icon = QIcon(prePath.joinpath(icon_name + '.jpg').as_posix())
        self.setIcon(self.icon)
        self.setToolTip(action_name)
        self.setFixedSize(QSize(size[0], size[0]))
        self.setIconSize(QSize(size[0], size[0]))


class ExternalCameraDisplay(CameraViewWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.centeringButton = LocalIconButton(
            icon_name="CenteringButton", action_name="choose new centerpoint"
        )
        self.centeringButton.clicked.connect(self.center_calibrator)
        self.layout_control.addWidget(self.centeringButton)

        self.projectionCalibration = LocalIconButton(
            icon_name="CalibrationButton", action_name="calibrate projection"
        )
        self.projectionCalibration.clicked.connect(self.stimulus_calibration)
        self.layout_control.addWidget(self.projectionCalibration)

        image_sock = self.experiment.return_image_socket()
        if image_sock is not None:
            self.centering_socket_number = image_sock
            self.centering_context = zmq.Context()
            self.centering_socket = self.centering_context.socket(zmq.PUB)
            self.centering_socket.bind(str("tcp://*:")+str(self.centering_socket_number))

    def stimulus_calibration(self):
        print('pressed it')

    def center_calibrator(self):
        print('pressed it 2')


class ExternalTrackingExperimentWindow(TrackingExperimentWindow):
    def __init__(self, *args, **kwargs):

        super().__init__(*args,  **kwargs)

        self.camera_display = ExternalCameraDisplay(experiment=kwargs["experiment"])

        self.monitoring_widget = QWidget()
        self.monitoring_layout = QVBoxLayout()
        self.monitoring_widget.setLayout(self.monitoring_layout)

        self.stream_plot = MultiStreamPlot(experiment=self.experiment)

        self.monitoring_layout.addWidget(self.stream_plot)

        self.extra_widget = (self.experiment.pipeline.extra_widget(
            self.experiment.acc_tracking)
                             if self.experiment.pipeline.extra_widget is not None
                             else None)

        # Display dropdown
        self.drop_display = ControlCombo(
            self.experiment.pipeline.all_params["diagnostics"],
        "image")

        if hasattr(self.camera_display, "set_pos_from_tree"):
            self.drop_display.control.currentTextChanged.connect(
                self.camera_display.set_pos_from_tree)

        # Tracking params button:
        self.button_tracking_params = IconButton(
            icon_name="edit_tracking", action_name="Change tracking parameters"
        )
        self.button_tracking_params.clicked.connect(self.open_tracking_params_tree)

        self.camera_display.layout_control.addStretch(10)
        self.camera_display.layout_control.addWidget(self.drop_display)
        self.camera_display.layout_control.addWidget(self.button_tracking_params)

        self.track_params_wnd = None

        self.status_display.addMessageQueue(self.experiment.frame_dispatcher.message_queue)


class ExternalTrackingExperiment(TrackingExperiment):
    def __init__(self,
                 image_socket=None,
                 go_socket=None,
                 timing_socket=None,
                 saving_socket=None,
                 automated=False,
                 *args,
                 **kwargs
                 ):

        self.need_image = False

        self.image_socket = image_socket
        self.go_socket = go_socket
        self.timing_socket = timing_socket
        self.saving_socket = saving_socket

        self.automated = automated

        super().__init__(*args, **kwargs)

    def get_image(self):
        return self.frame_dispatcher[0]

    def return_image_socket(self):
        return self.image_socket

    def end_protocol(self):
        super().end_protocol()
        try:
            # a ZMQ socket to send out that we've finished up here
            sending_context = zmq.Context()
            self.ending_socket = sending_context.socket(zmq.REQ)
            self.ending_socket.connect('tcp://localhost:' + str(self.saving_socket))
            self.ending_socket.send_string('True')
            self.ending_socket.recv_string()
            self.ending_socket.close()
        except:
            pass

    def make_window(self):
        self.window_main = ExternalTrackingExperimentWindow(experiment=self)
        self.window_main.construct_ui()
        self.initialize_plots()
        self.window_main.show()
        self.restore_window_state()

        if self.automated:
            self.start_protocol()


def stytra_container(image_socket=5558, go_button_socket=5559, time_socket=6000, camera_rot=-2, roi=None, savedir=None):
    """
    package the stytra classes together and run as a pyqt application

    uses ZMQ sockets to communicate around

    :param image_socket: for sending raw images for calibration or grabbing XY positions
    :param go_button_socket: links the stytra go button
    :param time_socket: socket for the timing information
    :param camera_rot: rotates the camera image (rig specific)
    :param roi: controls camera field of view
    :param savedir: initializes stytra saving path
    """
    if roi is None:
        roi = [0, 0, 1120, 1120]

    def stimCloser():
        """
        this is kinda janky - stytra auto opens a stimulus window, so we grab it and close it

        should be an easier way to just not open it ?
        """
        time.sleep(5)
        gw.getWindowsWithTitle('Stytra stimulus display')[0].close()

    stimWindowCloser = tr.Thread(target=stimCloser)
    stimWindowCloser.start()

    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    protocol = StytraDummy()
    exp = ExternalTrackingExperiment(protocol=protocol, app=app,dir_save=savedir,
                             tracking=dict(method='fish', embedded=False, estimator="position"),
                             camera=dict(type='spinnaker', min_framerate=155, rotation=camera_rot, roi=roi),
                             image_socket=image_socket, go_socket=go_button_socket, timing_socket=time_socket
                             )
    exp.start_experiment()
    app.exec_()
    stimWindowCloser.join()


if __name__ == '__main__':
    stytra_container()