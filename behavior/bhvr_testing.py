from pandastim.behavior import Tracking, Protocol
from pandastim.utils import port_provider
from pandastim.stimuli import BehavioralStimuli

import multiprocessing as mp
import threading as tr

stim_params = {
    'light_value' : 255,
    'dark_value' : 0,
    'frequency' : 32,
    'center_width' : 16,
    'strip_angle' : 0,
    'center_x' : 0,
    'center_y' : 0,
    'scale' : 8,
    'rotation_offset' : 90,
    'center_dot_size' : 5,
    'window_size' : (1024, 1024),
    'window_position' : (2432, 0),
    'fps' : 60,
    'window_undecorated' : True,
    'window_foreground' : True,
    'window_title' : 'Pandastim',
    'profile_on' : False

}
# this is just a small wrapper
def stim(_ports):
    behavioral_stimuli = BehavioralStimuli(stimuli=None, defaults=stim_params)

    # the panda3d event handler will not work across processes, but will across threads
    # protocol_thread = tr.Thread(target=Protocol.BaseProtocol, args=(None, _ports, stim_params))
    protocol_thread = tr.Thread(target=Protocol.CenterClickTestingProtocol, args=(None, _ports, stim_params))

    protocol_thread.start()

    behavioral_stimuli.run()

    protocol_thread.join()
    print('joined')

if __name__ == '__main__':

    _ports = {}
    keys = ['image_socket', 'go_socket', 'timing_socket', 'saving_socket', 'tracking_socket']
    for key in keys:
        _ports[key] = str(port_provider())

    print(_ports)

    camera_rot = -1
    roi = None
    savedir = None

    stytra_process = mp.Process(target=Tracking.stytra_container, args=(_ports, camera_rot, roi, savedir))
    stimuli_process = mp.Process(target=stim, args=(_ports,))

    stytra_process.start()
    stimuli_process.start()

    stytra_process.join()

    if not stytra_process.is_alive():
        stimuli_process.terminate()
        stimuli_process.join()
