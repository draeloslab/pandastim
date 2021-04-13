import numpy as np
import pandas as pd
import multiprocessing as mp

from pandastim import textures, stimuli, utils


def create_prot():

    duration = 15
    stat_time = 0
    repeats = 10

    _dic = {'stim_type': ['blank','s'], "frequency": [32,32], "angle": [0,0], "velocity": [0,0]}

    df = pd.DataFrame(_dic)

    df.loc[:, 'stationary_time'] = stat_time
    df.loc[:, 'duration'] = duration

    df = pd.concat([df] * repeats, ignore_index=True)
    return df


svepath = 'temp1.txt'

tex_size = (1024, 1024)
freqs = np.arange(101)

input_textures = {'freq': {}, 'blank': textures.BlankTexXY(texture_size=tex_size)}
for f in freqs:
    input_textures['freq'][f] = textures.GratingGrayTexXY(texture_size=tex_size, spatial_frequency=f)



def stims(port="5005"):
    stimulation = stimuli.ClosedLoopStimChoice(textures=input_textures, save_path=svepath)

    sub = utils.Subscriber(topic="stim", port=port)
    monitor = utils.MonitorDataPass(sub)
    stimulation.run()


if __name__ == '__main__':
    port1 = utils.port_provider()
    stims_proc = mp.Process(target=stims, args=(port1,))
    sequencer = mp.Process(target=utils.sequence_runner, args=(create_prot(), port1))
    stims_proc.start()
    sequencer.start()
    sequencer.join()
    stims_proc.join()

    if not sequencer.is_alive():
        stims_proc.terminate()
