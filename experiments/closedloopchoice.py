import numpy as np

from pandastim import textures, stimuli, utils


tex_size = (1024, 1024)
freqs = np.arange(101)

input_textures = {'freq': {}, 'blank': textures.BlankTexXY(texture_size=tex_size)}
for f in freqs:
    input_textures['freq'][f] = textures.GratingGrayTexXY(texture_size=tex_size, spatial_frequency=f)


stimulation = stimuli.ClosedLoopStimChoice(textures=input_textures)

if __name__ == '__main__':

    sub = utils.Subscriber(topic="stim", port="5005")
    monitor = utils.MonitorDataPass(sub)
    stimulation.run()