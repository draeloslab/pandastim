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
        self.experiment_trigger_comm.bind('tcp://*:' + str(ports['go_socket']))

        # these are subscribers to information exported from stytra
        self.position_comm = utils.Subscriber(port=ports['tracking_socket'])
        self.timing_comm = utils.Subscriber(port=ports['timing_socket'])

        self.experiment_running = False
        self.fish_data = []

        self.run_experiment()

    def run_experiment(self):
        # this should hang here until we handshake
        msg = self.experiment_trigger_comm.recv_string()
        self.experiment_trigger_comm.send_string('stim', zmq.SNDMORE)
        self.experiment_trigger_comm.send_pyobj(['GO'])
        print('experiment began')
        self.experiment_running = True

        data_stream = tr.Thread(target=self.stream_data,)
        data_stream.start()

    def stream_data(self):
        while self.experiment_running:
            print('asdf;lkj')
            topic = self.position_comm.socket.recv_string()
            data = self.position_comm.socket.recv_pyobj()
            print('asdlkfj;')
            self.fish_data.append(data)
            print(self.fish_data[0][0] == 'nan', self.fish_data[0][0] == np.nan)
