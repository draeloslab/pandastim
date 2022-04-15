from pandastim import  textures
from dataclasses import dataclass

from direct.showbase import DirectObject
from direct.showbase.MessengerGlobal import messenger

import threading as tr

import inspect


@dataclass(frozen=True)
class StimulusDetails:
    '''Contains details about a given stimulus'''
    stim_name: str


@dataclass(frozen=True)
class MonocularStimulusDetails(StimulusDetails):
    '''Contains details about a given stimulus'''
    # required
    stim_name: str
    angle: int
    velocity: int

    # defaults
    frequency: int = 60
    stationary_time: int = 0
    duration: int = -1  # defaults to going forever
    light_value: int = 0
    dark_value: int = 0
    texture_size: tuple = (1024, 1024)

    texture: textures.TextureBaseXY = textures.GratingGrayTexXY(texture_size=texture_size,
                                                                spatial_frequency=frequency,
                                                                dark_val=dark_value,
                                                                light_val=light_value)

    def __post_init__(self):
        """Because python isn't static lets force things here"""
        acceptedTypes = {self.stim_name: str,
                         self.angle: float,
                         self.velocity: float,
                         self.frequency: int,
                         self.stationary_time: int,
                         self.duration: int,
                         self.light_value: int,
                         self.dark_value: int,
                         self.texture_size: tuple,
                         self.texture: textures.TextureBaseXY}

        for k, v in acceptedTypes.items():
            assert (isinstance(k, v)), f'{k} must be {v}'


@dataclass(frozen=True)
class BinocularStimulusDetails(StimulusDetails):
    '''Contains details about a given stimulus'''
    # required
    stim_name: str
    angle: tuple
    velocity: tuple

    # defaults
    frequency: tuple = (60, 60)
    stationary_time: tuple = (0, 0)
    duration: tuple = (-1, -1)  # defaults to going forever
    light_value: tuple = (0, 0)
    dark_value: tuple = (0, 0)
    texture_size: tuple = (1024, 1024)

    texture: tuple = (textures.GratingGrayTexXY(texture_size=texture_size,
                                                spatial_frequency=frequency[0],
                                                dark_val=dark_value[0],
                                                light_val=light_value[0]),
                      textures.GratingGrayTexXY(texture_size=texture_size,
                                                spatial_frequency=frequency[1],
                                                dark_val=dark_value[1],
                                                light_val=light_value[1])

                      )

    def __post_init__(self):
        """Because python isn't static lets force things here"""
        acceptedTypes = {self.stim_name: str,
                         self.angle: tuple,
                         self.velocity: tuple,
                         self.frequency: tuple,
                         self.stationary_time: tuple,
                         self.duration: tuple,
                         self.light_value: tuple,
                         self.dark_value: tuple,
                         self.texture_size: tuple}

        for k, v in acceptedTypes.items():
            assert (isinstance(k, v)), f'{k} must be {v}'


@dataclass
class LiveStimulusDetails:
    '''pandastim writes into here live'''
    stimulus_details: StimulusDetails
    motion: bool = False


### Update this bad boy
### mostly the live/load aspect
class DetailsReceiver(DirectObject.DirectObject):
    def __init__(self, subscriber):
        self.sub = subscriber
        self.run_thread = tr.Thread(target=self.run)
        self.running = True
        self.currentStimClass = {'stim_name': None}
        self.run_thread.start()

    def run(self):
        # this is run on a separate thread so it can sit in a loop waiting to receive messages
        while self.running:
            topic = self.sub.socket.recv_string()
            data = self.sub.socket.recv_pyobj()

            if 'stim_name' not in data:
                try:
                    data['stim_name'] = f'{data["angle"]}_{data["velocity"]}_{data["frequency"]}'
                except KeyError:
                    data['stim_name'] = f'{data["angle"]}_{data["velocity"]}_'

            if 'load' in data:
                self.create_stim_details(data)
            elif 'live' in data and data['stim_name'] == self.currentStimClass.stim_name:
                messenger.send('stimulus_update', [self.currentStimClass])
            elif 'live' in data and data['stim_name'] != self.currentStimClass.stim_name:
                self.create_stim_details(data)
                messenger.send('stimulus_update', [self.currentStimClass])

    def create_stim_details(self, data):
        if data['stim_type'] == 's':
            detail_dict = {k: v for k, v in data.items() if
                           k in list(inspect.signature(MonocularStimulusDetails).parameters)}
            self.currentStimClass = MonocularStimulusDetails(**detail_dict)
        elif data['stim_type'] == 'b':
            detail_dict = {k: v for k, v in data.items() if
                           k in list(inspect.signature(BinocularStimulusDetails).parameters)}
            self.currentStimClass = BinocularStimulusDetails(**detail_dict)

    def kill(self):
        self.running = False
