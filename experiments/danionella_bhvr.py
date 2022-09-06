from pandastim.utils import port_provider, load_params
from pandastim.stimuli import Behavior
from pandastim.behavior.Protocol import wrapper, ClosedLoopProtocol
from pandastim.behavior.Tracking import stytra_container

import multiprocessing as mp

import sys

from pathlib import Path

# parameter_path = r'C:\Soft_Kitty\Anaconda3\envs\cleanStytra\Lib\site-packages\pandastim\resources\matt_rig2_exp_params.json'
parameter_path = Path(sys.executable).parents[0].joinpath(r'Lib\site-packages\pandastim\resources\rig_params.json')
stimulus_path = Path(sys.executable).parents[0].joinpath(r'Lib\site-packages\pandastim\resources\sevenrep_17stim_python37.hdf')
# stimulus_path = r'C:\Soft_Kitty\Anaconda3\envs\cleanStytra\Lib\site-packages\pandastim\resources\monocFB.hdf'

import argparse, os

# def dir_path(string):
#         if os.path.isdir(string):
#                 return string
#         else:
#                 raise NotADirectoryError(string)

parser = argparse.ArgumentParser(description='please input path')
parser.add_argument('--path')

if __name__ == '__main__':

        _ports = {}
        keys = ['image_socket', 'go_socket', 'timing_socket', 'saving_socket', 'tracking_socket']
        for key in keys:
                _ports[key] = str(port_provider())

        params = load_params(parameter_path)

        camera_rot = params['camera_rotation']
        roi = params['roi']
        args = parser.parse_args()
        savedir = Path(args.path)

        stytra_process = mp.Process(target=stytra_container, args=(_ports, camera_rot, roi, savedir,))
        stimulus_process = mp.Process(target=wrapper, args=(ClosedLoopProtocol, Behavior, stimulus_path, _ports, params))

        stimulus_process.start()
        stytra_process.start()

        stytra_process.join()

        if not stytra_process.is_alive():
                stimulus_process.terminate()
                stimulus_process.join()
