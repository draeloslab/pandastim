try:
    from pandastim import stimuli, utils
except ModuleNotFoundError:
    import sys
    sys.path.append(r'C:\soft\Anaconda3\envs\pstim\Lib\site-packages')
    from pandastim import stimuli, utils


def spawn_pandas(save_path=None, port=5005):

    stimulation = stimuli.ClosedLoopStimChoice(window_size=(1024,1024), gui=True, publisher_port=5008, live_update=True, save_path=save_path, debug=False)

    sub = utils.Subscriber(topic="stim", port=port)
    sub2 = utils.Subscriber(topic="stim", port=5006, ip=r"tcp://10.122.170.169:")
    sub3 = utils.Subscriber(topic="stim", port=5010)

    monitor = utils.MonitorDataPass(sub)
    monitor2 = utils.MonitorDataPass(sub2)
    monitor3 = utils.MonitorDataPass(sub3)

    stimulation.run()


if __name__ == '__main__':
    sve_pth = r'C:\data\pstim_stimuli/' + 'anne_stims.txt'
    spawn_pandas(save_path=sve_pth)
