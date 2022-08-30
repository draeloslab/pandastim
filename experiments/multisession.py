import sys
from pathlib import Path

import pandas as pd
from scopeslip import zmqComm
from tifffile import imread

from pandastim import utils
from pandastim.buddies import stimulus_buddies
from pandastim.stimuli import stimulus

t_image_path = r"D:\Data\Imaging\2022\anatomy_img_r6_16bit.tif"
t_image = imread(t_image_path)

myWalky = zmqComm.WalkyTalky(
    outputPort="5005", inputIP="tcp://10.122.170.21:", inputPort=4701
)
bud = stimulus_buddies.MultiSessionBuddy(
    walky_talky=myWalky, pauseHours=0.01, target_image=t_image
)

inputStimuli = pd.read_hdf(
    Path(sys.executable)
    .parents[0]
    .joinpath(
        r"Lib\site-packages\pandastim\resources\protocols\sevenrep_twentyonestim.hdf"
    )
)

inputStimuli = inputStimuli.loc[:2]  # in this case after 139 is blanks and repeats

print(inputStimuli)

stimSequence = utils.legacy2current(
    inputStimuli
)  # this converts the saved sequence into stim types

bud.queue = stimSequence

pstim = stimulus.ExternalStimulus(buddy=bud)

pstim.run()
