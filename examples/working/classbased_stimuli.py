import json

import pandas as pd
pd.options.mode.chained_assignment = None

from pandastim import textures, stimuli
import logging




# this loads in your default parameters
p = r'C:\Users\matt_analysis\Documents\def_pstim_params.txt'
with open(p) as json_file:
    pstim_params = json.load(json_file)

# make a cute little stim dict
t_size = (512,512)
fwd = {'stim_type' : 's', 'velocity' : 0.02, 'angle' : 0, 'stationary_time':1, 'duration' : 3, 'texture' : textures.GratingGrayTexXY(texture_size=t_size, spatial_frequency=20)}
right = {'stim_type' : 'b', 'velocity' : [0.02, -0.02],'angle' : [90, 25], 'duration' : [5, 2], 'texture' : [textures.GratingGrayTexXY(texture_size=t_size, spatial_frequency=20), textures.GratingGrayTexXY(texture_size=t_size, spatial_frequency=20)]}
left = {'stim_type' : 's', 'velocity' : 0.02,'angle' : 270, 'duration' : 5, 'texture' : textures.GratingGrayTexXY(texture_size=t_size)}
stims = pd.DataFrame([fwd, right, left]*3)


# openLoop = stimuli.OpenLoopStimulus(stimuli=stims, defaults=pstim_params)

openLoop = stimuli.MonocularImprov(input_port=5009)
openLoop.run()
