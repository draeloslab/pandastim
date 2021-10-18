'''
this setup uses the stytra package for fish tracking:

https://github.com/portugueslab/stytra

'''
import zmq
import time
import qdarkstyle
import sys
import zarr
import uuid

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

from pandastim.utils import Publisher, port_provider


# stuff to run a stytra window and communicate with pandas
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
        # this only runs the first time
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

        data = np.array(self._experiment.estimator.get_position())
        self._experiment.pstim_pub.socket.send_string('stim')
        self._experiment.pstim_pub.socket.send_pyobj(data)

        # only update every 50 loop runs, this runs at ~30-40 Hz, hurts performance to do more often
        self.iterator += 1
        if self.iterator > 100:
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
            icon_name="CalibrationButton", action_name="Calibrate Projection"
        )
        self.projectionCalibration.clicked.connect(self.stimulus_calibration)
        self.layout_control.addWidget(self.projectionCalibration)

        self.calibrationStimulus = LocalIconButton(
            icon_name="CalibrationMode", action_name="swap to calibration stimulus"
        )
        self.calibrationStimulus.clicked.connect(self.calibration_stimulus)
        self.layout_control.addWidget(self.calibrationStimulus)

        image_sock = self.experiment.return_image_socket()
        if image_sock is not None:
            self.centering_socket_number = image_sock
            self.centering_context = zmq.Context()
            self.centering_socket = self.centering_context.socket(zmq.PUB)
            self.centering_socket.bind(str("tcp://*:")+str(self.centering_socket_number))

    def stimulus_calibration(self):
        print('centering')
        topic = 'centering'
        self.msg_sender(self.centering_socket, self.image_item.image, topic)

    def center_calibrator(self):
        print('calibrating')
        topic = 'calibration'
        self.msg_sender(self.centering_socket, self.image_item.image, topic)

    def calibration_stimulus(self):
        print('calibration_stimulus on')
        topic = 'calibrationStimulus'
        self.msg_sender(self.centering_socket, 'calibration_triangles', topic)

    @staticmethod
    def msg_sender(sock, img, string, flags=0, image=True):
        if image:
            my_msg = dict(dtype=str(img.dtype), shape=img.shape)
            sock.send_string(string, flags | zmq.SNDMORE)
            sock.send_json(my_msg, flags | zmq.SNDMORE)
            return sock.send(img, flags)
        else:
            sock.send_string(flags, zmq.SNDMORE)
            sock.send_pyobj([img])


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
    def __init__(self, ports, automated=False,
                 *args,
                 **kwargs
                 ):

        self.need_image = False

        self.image_socket = ports['image_socket']
        self.go_socket = ports['go_socket']
        self.timing_socket = ports['timing_socket']
        self.saving_socket = ports['saving_socket']
        self.pstim_pub = Publisher(str(ports['tracking_socket']))

        self.automated = automated

        super().__init__(*args, **kwargs)


    def get_image(self):
        return self.frame_dispatcher[0]

    def return_image_socket(self):
        return self.image_socket

    def end_protocol(self, save=True):
        super().end_protocol()

    def make_window(self):
        self.window_main = ExternalTrackingExperimentWindow(experiment=self)
        self.window_main.construct_ui()
        self.initialize_plots()
        self.window_main.show()
        self.restore_window_state()

        if self.automated:
            self.start_protocol()


def stytra_container(ports, camera_rot=-2, roi=None, savedir=None):
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

        we are running a stim to handle the time tho
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
                             camera=dict(type='spinnaker', min_framerate=155, rotation=camera_rot, roi=roi), ports=ports
                             )
    exp.start_experiment()
    app.exec_()
    stimWindowCloser.join()


if __name__ == '__main__':

    _ports = {}
    keys = ['image_socket', 'go_socket', 'timing_socket', 'saving_socket', 'tracking_socket']
    for key in keys:
        _ports[key] = port_provider()

    stytra_container(ports=_ports, savedir=r'D:\testingdata')
