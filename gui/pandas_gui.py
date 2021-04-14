from PyQt5 import QtWidgets, uic
from PyQt5.Qt import QApplication

from pandastim import textures, stimuli, utils

import qdarkstyle
import zmq
import numpy as np
import multiprocessing as mp
import threading as tr
import time
import os
import sys


exit_event = tr.Event()

class PandasController(QtWidgets.QMainWindow):
    def __init__(self):
        super(PandasController, self).__init__()

        self.locPath  = os.path.dirname(os.path.realpath(__file__))
        self.UIpath = os.path.join(self.locPath, 'gui_layout.ui')
        uic.loadUi(self.UIpath, self)

        self.show()
        self.updateButton.clicked.connect(self.update_stimuli)
        # QtWidgets.QCheckBox.

        self.pandas_port = utils.port_provider()

        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PUB)
        self._socket.bind('tcp://*:' + str(self.pandas_port))
        self.stimulus_topic = 'stim'

        self.max_frequency = 200
        self.running = True

        self.pandas = mp.Process(target=self.spawn_pandas, args=(self.pandas_port, self.max_frequency,))
        self.pandas.start()

        self.wf_freq.setMaximum(self.max_frequency)

        self.live_updater = tr.Thread(target=self.live_updater)
        self.live_updater.dameon = True
        self.live_updater.start()

    def update_stimuli(self):
        curr_tab = self.tabs.currentIndex()
        if curr_tab == 0:
            stim = {'stim_type': 's', 'angle': self.wf_angle.value(), 'velocity': self.wf_vel.value(),
                    'stationary_time': self.wf_stat.value(), 'stim_time': self.wf_stim_time.value(), 'freq': self.wf_freq.value()}
            self._socket.send_string(self.stimulus_topic, zmq.SNDMORE)
            self._socket.send_pyobj(stim)
        if curr_tab == 1:
            stim = {
                'stim_type': 'b', 'angle': [self.b_angle_0.value(), self.b_angle_1.value()],
                'velocity': [self.b_vel_0.value(), self.b_vel_1.value()],
                'stationary_time': [self.b_stat_0.value(), self.b_stat_1.value()],
                'stim_time': [self.b_t_0.value(), self.b_t_1.value()],
                'freq': [self.b_freq_0.value(), self.b_freq_1.value()],
                'center_width' : self.b_center_width.value(),
                'center_x': self.ctr_x.value(),
                'center_y': self.ctr_y.value(),
                'strip_angle': self.strip_angle.value()
                    }
            self._socket.send_string(self.stimulus_topic, zmq.SNDMORE)
            self._socket.send_pyobj(stim)
        if curr_tab == 2:
            stim = {
                'stim_type': 'rdk'

            }

    def live_updater(self):
        while self.running:
            curr_tab = self.tabs.currentIndex()

            if exit_event.is_set():
                self.running = False
                break

            if curr_tab == 0:
                self.last_sent = None
                while True:
                    if exit_event.is_set():
                        self.running = False
                        break

                    if self.liveUpdate.isChecked():
                        stim = {'stim_type': 's', 'angle': self.wf_angle.value(), 'velocity': self.wf_vel.value(),
                                'stationary_time': self.wf_stat.value(), 'stim_time': self.wf_stim_time.value(),
                                'freq': self.wf_freq.value()}
                        if stim != self.last_sent:
                            self._socket.send_string(self.stimulus_topic, zmq.SNDMORE)
                            self._socket.send_pyobj(stim)
                            self.last_sent = stim
                        else:
                            pass
                    else:
                        break
                    time.sleep(0.02)

            elif curr_tab == 1:
                self.last_sent = None
                while True:
                    if exit_event.is_set():
                        self.running = False
                        break

                    if self.liveUpdate.isChecked():
                        stim = {
                            'stim_type': 'b', 'angle': [self.b_angle_0.value(), self.b_angle_1.value()],
                            'velocity': [self.b_vel_0.value(), self.b_vel_1.value()],
                            'stationary_time': [self.b_stat_0.value(), self.b_stat_1.value()],
                            'stim_time': [self.b_t_0.value(), self.b_t_1.value()],
                            'freq': [self.b_freq_0.value(), self.b_freq_1.value()],
                            'center_width' : self.b_center_width.value(),
                            'center_x' : self.ctr_x.value(),
                            'center_y' : self.ctr_y.value(),
                            'strip_angle': self.strip_angle.value()
                                }
                        if stim != self.last_sent:
                            self._socket.send_string(self.stimulus_topic, zmq.SNDMORE)
                            self._socket.send_pyobj(stim)
                            self.last_sent = stim
                        else:
                            pass
                    else:
                        break
                    time.sleep(0.02)

            time.sleep(0.005)
        return

    def closeEvent(self, event):
        self.running = False
        self.pandas.terminate()
        exit_event.set()
        self.close()

    @staticmethod
    def spawn_pandas(port=5005, freq_max=101):
        tex_size = (1024, 1024)
        freqs = np.arange(freq_max)

        input_textures = {'freq': {}, 'blank': textures.BlankTexXY(texture_size=tex_size)}
        for f in freqs:
            input_textures['freq'][f] = textures.GratingGrayTexXY(texture_size=tex_size, spatial_frequency=f)

        stimulation = stimuli.ClosedLoopStimChoice(textures=input_textures, gui=True)

        sub = utils.Subscriber(topic="stim", port=port)
        monitor = utils.MonitorDataPass(sub)
        stimulation.run()


def run():
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    wind = PandasController()
    wind.show()
    app.exec()


if __name__ == '__main__':
    run()