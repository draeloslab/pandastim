from pandastim import stimuli

# baseline parameters for pstim
improv_params = {
    'light_value' : 255,
    'dark_value' : 0,
    'frequency' : 32,
    'center_width' : 16,
    'strip_angle' : 0,
    'center_x' : 0,
    'center_y' : 0,
    'scale' : 8,
    'rotation_offset' : -90,
    'window_size' : (1024, 1024),
    'window_position' : (2400, 270),
    'fps' : 60,
    'window_undecorated' : True,
    'window_foreground' : True,
    'window_title' : 'Pandastim',
    'profile_on' : False

}

sve_pth = r'C:\data\pstim_stimuli/' + 'anne_stims.txt'

# set up com ports
_port = 5006
_ip = r"tcp://10.122.170.169:"
publishing_port = 5009

stimulation = stimuli.MonocularImprov(defaults=improv_params,
                                      input_port=_port,
                                      input_ip=_ip,
                                      output_port=publishing_port)

stimulation.run()
