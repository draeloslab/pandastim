from pandastim.working.behavior import Tracking, Protocol
from pandastim.utils import port_provider

import multiprocessing as mp


if __name__ == '__main__':

    _ports = {}
    keys = ['image_socket', 'go_socket', 'timing_socket', 'saving_socket', 'tracking_socket']
    for key in keys:
        _ports[key] = port_provider()

    print(_ports)

    camera_rot = -2
    roi = None
    savedir = None

    p1 = mp.Process(target=Tracking.stytra_container, args=(_ports, roi, savedir))
    p2 = mp.Process(target=Protocol.BaseProtocol, args=(None, _ports, ))

    p1.start()
    p2.start()
    p1.join()

    if not p1.is_alive():
        p2.terminate()
        p2.join()
