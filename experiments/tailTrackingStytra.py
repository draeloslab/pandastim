# stytra imports
from stytra.stimulation.stimuli import Stimulus
from stytra import Protocol
from stytra.experiments.tracking_experiments import TrackingExperiment

from PyQt5.QtWidgets import QApplication

import time
import qdarkstyle
import zmq

import threading as tr
import pygetwindow as gw
import multiprocessing as mp


# this is the Stytra stimulus, which we're not presenting, but we're using to update time
class BlankUpdater(Stimulus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self):
        pass


# blankest Stytra protocol.
class DummyStytra(Protocol):
    name = "dummy"

    def __init__(self,):
        super().__init__()

    def get_stim_sequence(self):
        return [BlankUpdater(duration=30)]


# the physical function to put the above 2 classes together and run stytra, runs stytra as a pyqt application
def stytra_container(camera_rot=-2, roi=None, savedir=None):
    if roi is None:
        roi = [262, 586, 1120, 1120]

    def fixer():
        time.sleep(5)
        gw.getWindowsWithTitle('Stytra stimulus display')[0].close()

    a = tr.Thread(target=fixer)
    a.start()

    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    protocol = DummyStytra()
    exp = TrackingExperiment(protocol=protocol, app=app, dir_save=savedir,
                             tracking=dict(method='tail', embedded=True),
                             camera=dict(type='spinnaker'),
                             )
    exp.start_experiment()
    app.exec_()
    a.join()


def trackingDataReceiver():
    time.sleep(5)
    numberPath = r'C:\soft\Anaconda3\envs\pstim\Lib\site-packages\pandastim\resources\portNumber.dat'
    with open(numberPath) as file:
        for line in file:
            lst = line.split()
    port = str(lst[0])
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'tailTracking')
    socket.connect("tcp://localhost:" + port)
    print('using port ', port)
    while True:
        topic = socket.recv_string()
        msgs = socket.recv_pyobj()
        print(msgs)


if __name__ == '__main__':

    stytra = mp.Process(target=stytra_container)
    receiver = mp.Process(target=trackingDataReceiver)

    stytra.start()
    receiver.start()

    stytra.join()
    if not stytra.is_alive():
        receiver.terminate()
