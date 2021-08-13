import numpy as np
import pandas as pd
import multiprocessing as mp

from pandastim import textures, stimuli, utils


def create_prot():
    stim_types = []
    velocities = []
    angles = []
    frequencies = []



    _freqs = np.arange(2,100,16)
    _angles = np.arange(0,360,45)
    _vels = np.arange(0,0.21,0.04)

    _freqs = np.arange(2, 100, 16)
    _angles = np.arange(0, 360, 45)
    _vels = np.arange(0, 0.21, 0.04)


    # monoc first
    for f in _freqs:
        for theta in _angles:
            for v in _vels:
                stim_types.append('s')
                frequencies.append(f)
                angles.append(theta)
                velocities.append(-v)

    _bin_angles = _angles[::2]
    _bin_freqs = _freqs[2:-1]
    _bin_vels = _vels[2:-2]

    # binoc time
    for f in _bin_freqs:
        for theta in _bin_angles:
            for v in _bin_vels:
                stim_types.append('b')
                frequencies.append([f,f])
                angles.append([theta,theta])
                velocities.append([-v,-v])

    for f in _bin_freqs:
        for theta in _bin_angles:
            for v in _bin_vels:
                stim_types.append('b')
                frequencies.append([f, f])
                angles.append([theta, theta])
                velocities.append([0, -v])

    for f in _bin_freqs:
        for theta in _bin_angles:
            for v in _bin_vels:
                stim_types.append('b')
                frequencies.append([f, f])
                angles.append([theta, theta])
                velocities.append([-v, 0])

    _dic = {'stim_type': stim_types, "frequency": frequencies, "angle": angles, "velocity": velocities}


    df = pd.DataFrame(_dic)
    df = df.sample(frac=1).reset_index(drop=True)

    duration = 7
    stat_time = 18

    df.loc[:, 'stationary_time'] = stat_time
    df.loc[:, 'duration'] = duration
    df = pd.concat([df]*3, ignore_index=True)
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
