from direct.showbase import DirectObject
from direct.showbase.MessengerGlobal import messenger

from pandastim import utils

import zmq

import threading as tr
import numpy as np


class BaseProtocol(DirectObject.DirectObject):
    def __init__(self, stimuli, ports):

        self.stimuli = stimuli

        # set up handshake communication with stytra for experiment triggering
        self.experiment_trigger_context = zmq.Context()
        self.experiment_trigger_comm = self.experiment_trigger_context.socket(zmq.REP)
        self.experiment_trigger_comm.bind('tcp://*:' + ports['go_socket'])

        # this receives positional information from sytra
        self.position_comm = utils.Subscriber(port=ports['tracking_socket'])

        # this port is used for centering, calibrating, and toggling calibration stimulus
        self.stytra_cam_output_port = utils.Subscriber(ports['image_socket'])
        self.cam_outputs_thread = tr.Thread(target=self.centering_calibration)

        # this is used to publish timing information to update the stytra loading bar
        self.timing_comm = utils.Publisher(port=ports['timing_socket'])

        self.experiment_running = False
        self.experiment_finished = False
        self.fish_data = []

        self.cam_outputs_thread.start()

        self.run_experiment()

    def run_experiment(self):
        # this should hang here until we handshake
        msg = self.experiment_trigger_comm.recv_string()
        self.experiment_trigger_comm.send_string('stim', zmq.SNDMORE)
        self.experiment_trigger_comm.send_pyobj(['GO'])
        print('experiment began')
        self.experiment_running = True

        data_stream = tr.Thread(target=self.position_receiver,)
        data_stream.start()

    def position_receiver(self):
        while self.experiment_running:
            topic = self.position_comm.socket.recv_string()
            data = self.position_comm.socket.recv_pyobj()
            self.fish_data.append(data)
            print(self.fish_data[0][0] == 'nan', self.fish_data[0][0] == np.nan)

    def centering_calibration(self):
        while not self.experiment_finished:
            topic = self.stytra_cam_output_port.socket.recv_string()
            if topic == 'calibrationStimulus':
                ## this will be a toggled string on/off
                msg = self.stytra_cam_output_port.socket.recv_pyobj()[0]
                toggle_direction = msg.split('_')[-1]

                if toggle_direction == 'on':
                    messenger.send('calibration_stimulus', [True])
                elif toggle_direction == 'off':
                    messenger.send('calibration_stimulus', [False])
            else:
                ## this will be images
                image = utils.img_receiver(self.stytra_cam_output_port.socket)
                if topic == 'calibration':
                    # run the calibration fxn
                    print('calibrating', image)
                elif topic == 'centering':
                    # do the opencv thingydo
                    print('centering', image)
