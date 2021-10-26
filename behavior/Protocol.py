from direct.showbase import DirectObject
from direct.showbase.MessengerGlobal import messenger

from pandastim import utils, textures
from pandastim.behavior import calibration

import zmq
import cv2

import threading as tr
import numpy as np
import pygetwindow as gw


class BaseProtocol(DirectObject.DirectObject):
    def __init__(self, stimuli, ports, defaults):

        self.stimuli = stimuli
        self.defaults = defaults

        self.centered_pt = (512, 512)

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
        try:
            self.proj2cam, self.cam2proj = calibration.load_params()
        except FileNotFoundError:
            print("CALIBRATION FILE NOT FOUND, EXITING")
            import sys
            sys.exit()

        self.experiment_running = True

        data_stream = tr.Thread(target=self.position_receiver,)
        data_stream.start()

    def position_receiver(self):
        while self.experiment_running:
            topic = self.position_comm.socket.recv_string()
            data = self.position_comm.socket.recv_pyobj()
            self.fish_data.append(data)
            # np.isnan(data[0])

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
                    try:
                        proj_to_camera, camera_to_proj = calibration.StimulusCalibrator(image).transforms()
                        calibration.save_params(proj_to_camera, camera_to_proj)
                        print('CALIBRATION SAVED: ', proj_to_camera)

                    except Exception as e:
                        print('failed to calibrate', e)

                elif topic == 'centering':
                    image -= 3
                    image[image < 0] = 0
                    image = np.array(image)

                    def draw(event, x, y, flags, params):
                        if event==1:
                            cv2.line(image, pt1=(x,y), pt2=(x,y), color=(255,255,255), thickness=3)
                            cv2.destroyAllWindows()
                    cv2.namedWindow('centerWindow')
                    cv2.setMouseCallback('centerWindow', draw)

                    # opencv windows like to pop up in the background, this is hacky but brings it to front
                    centering_window = gw.getWindowsWithTitle('centerWindow')[0]
                    centering_window.minimize()
                    centering_window.restore()
                    centering_window.maximize()

                    cv2.imshow('centerWindow', image)
                    cv2.waitKey(0)
                    # lots of destroying the window so opencv cant stick around :)
                    cv2.destroyAllWindows()

                    # we drew something max val on an image that contained no max vals, now we grab it
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(image)
                    self.centered_pt = np.array([max_loc[0], max_loc[1]])

                    print(self.centered_pt)

    # use the cam2proj
    def position_transformer(self, x, y):
        # swap order to flip xy
        pos = np.array([x, y])
        conv_pt = cv2.transform(np.reshape(pos, (1, 1, 2)), self.cam2proj)[0][0]

        a = conv_pt[0]
        b = conv_pt[1]

        x = -1 * ((a / self.defaults['window_size'][0]) - 0.5)
        y = -1 * ((b / self.defaults['window_size'][1]) - 0.5)

        return x, y


class CenterClickTestingProtocol(BaseProtocol):
    '''
    this testing protocol lets you click to move a circle to your click point
    '''
    def __init__(self, *args, **kwargs):
        self.last_stim = 9
        self.x, self.y = [0,0]
        super().__init__(*args, **kwargs)

    def run_experiment(self):
        super().run_experiment()
        stim = [0,
                {'stim_type' : 's', 'velocity' : 0, 'angle' : 0, 'texture' : textures.CircleGrayTex(circle_radius=3),
                 }]
        messenger.send('stimulus', [stim])
        self.show_tracking()

    def position_receiver(self):
        while self.experiment_running:
            topic = self.position_comm.socket.recv_string()
            data = self.position_comm.socket.recv_pyobj()
            self.show_tracking()

    def show_tracking(self):
        if self.x != self.centered_pt[0] and self.y != self.centered_pt[1]:
            self.x, self.y = self.centered_pt
            x,y = self.position_transformer(self.x, self.y)
            messenger.send('stimulus_update', [[x, y]])


class FishTrackerTestingProtocol(CenterClickTestingProtocol):
    '''
    this one moves a circle around under the fish
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def show_tracking(self):
        if not np.isnan(self.data[0]):
            _x = self.data[1]
            _y = self.data[0]
            x, y = self.position_transformer(_x, _y)
            messenger.send('stimulus_update', [[x, y]])
