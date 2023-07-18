import multiprocessing as mp
import sys
from pathlib import Path

import pandas as pd
import qdarkstyle
from PyQt5.Qt import QApplication
from scopeslip import zmqComm
from scopeslip.gui import alignment_gui
from tifffile import imread

from pandastim import utils
from pandastim.buddies import stimulus_buddies
from pandastim.stimuli import stimulus


def pstimWrapper():
    # 1 - edit your save path here
    mySavePath = r"E:\Pstim\test_output.txt"

    # parameters necessary for ROI to pop up, probably don't need to change
    paramspath = (
        Path(sys.executable)
        .parents[0]
        .joinpath(r"Lib\site-packages\pandastim\resources\params\default_params.json")
    )

    # handles communication with the default parameters, don't need to change
    stimBuddy = stimulus_buddies.StimulusBuddy(
        reporting="onMotion",
        default_params_path=paramspath,
        outputMethod="zmq",
        savePath=mySavePath,
    )

    # this uses stimulusBuddy to run open loop experiments
    inputStimuli = pd.read_hdf(
        Path(sys.executable)
        .parents[0]
        .joinpath(r"Lib\site-packages\pandastim\resources\protocols\medial_right.hdf"
            # r"Lib\site-packages\pandastim\resources\protocols\sevenrep_twentyonestim.hdf"
        )
    )
    # can augment your pstim file here in any way you want
    #inputStimuli = inputStimuli.loc[:139]

    # set duration and stationary time here
    stimSequence = utils.legacy2current(inputStimuli, duration=100000, stationary_time=5)
    stimBuddy.queue = stimSequence

    pstim = stimulus.ExternalStimulus(buddy=stimBuddy, params_path=paramspath)

    pstim.run()

if __name__ == "__main__":

    _processes = [pstimWrapper]

    processes = [mp.Process(target=p) for p in _processes]
    [p.start() for p in processes]
    [p.join() for p in processes]