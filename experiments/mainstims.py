import numpy as np
import pandas as pd
import multiprocessing as mp

from pandastim import textures, stimuli, utils


svepath = r'D:\duke_exp\matt\2021\volumes\v1_stims_good.txt'

tex_size = (1024, 1024)


freqs = np.arange(101)

# freqs = np.arange(50,70)

input_textures = {'freq': {}, 'blank': textures.BlankTexXY(texture_size=tex_size)}
for f in freqs:
    input_textures['freq'][f] = textures.GratingGrayTexXY(texture_size=tex_size, spatial_frequency=f)



def create_prot():
    # df = pd.read_hdf(r'C:\soft\Anaconda3\envs\pstim\Lib\site-packages\pandastim\experiments\new_stimulus_set.h5')
    df = pd.read_hdf(r'C:\soft\Anaconda3\envs\pstim\Lib\site-packages\pandastim\experiments\imaging.hdf')

    df = pd.concat([df]*10)
    df.reset_index(inplace=True)
    # df['duration'] = 7
    return df

def stims(port="5005"):
    stimulation = stimuli.ClosedLoopStimChoice(input_textures=input_textures, save_path=svepath)

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
