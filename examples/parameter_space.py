from pandastim import utils
from pandastim.stimuli import stimulus, stimulus_details, textures

import numpy as np

center_x = np.arange(405,1525,100)
center_y = np.arange(625,1285,100)
length = np.linspace(20,800, num=10).astype(int)
width = np.linspace(20,1600, num=10).astype(int)
frequency = np.linspace(1,120, num=12).astype(int)

ellipse1 = textures.EllipseGrayTex(
            texture_size = 1600, 
            frequency = 1,
            center_x= 1205,
            center_y= 925,
            width= 50,
            length= 50,
            texture_name='gray_ellipse',
            bg_intensity= 200,
            fg_intensity=50,
        )

ellipse2 = textures.EllipseGrayTex(
            texture_size = 1600, 
            frequency = 10,
            center_x= 605,
            center_y= 1125,
            width= 100,
            length= 100,
            texture_name='gray_ellipse',
            bg_intensity= 0, #black
            fg_intensity=200, #grey
        )

ellipse3 = textures.EllipseGrayTex(
            texture_size = 1600, 
            frequency = 10,
            center_x= 1305,
            center_y= 925,
            width= 300,
            length= 546,
            texture_name='gray_ellipse',
            bg_intensity= 255, #white
            fg_intensity=200, # grey
        )

ellipse4 = textures.EllipseGrayTex(
            texture_size = 1600, 
            frequency = 60,
            center_x= 800,
            center_y= 1000,
            width= 546,
            length= 400,
            texture_name='gray_ellipse',
            bg_intensity= 255, #white
            fg_intensity=0, # grey
        )


rect1 = textures.RectGrayTex(
            texture_size = 1600, 
            frequency = 60,
            center_x= 800,
            center_y= 1000,
            width= 546,
            length= 400,
            texture_name='gray_ellipse',
            bg_intensity= 255, #white
            fg_intensity=0, # grey
        )

rect2 = textures.RectGrayTex(
            texture_size = 1600, 
            frequency = 60,
            center_x= 800,
            center_y= 1000,
            width= 400,
            length= 400,
            texture_name='gray_ellipse',
            bg_intensity= 255, #white
            fg_intensity=0, # grey
        )



stim = [] 
for angle in range(0,361,30):
    stim.append(stimulus_details.MonocularStimulusDetails(
    texture=ellipse1,
    angle=angle,
    velocity=0.0,
    stationary_time=0,
    duration=1,
    hold_after=float(1),
    stim_name="gray_ellipse",
    ))

for angle in range(0,361,30):
    stim.append(stimulus_details.MonocularStimulusDetails(
    texture=ellipse2,
    angle=angle,
    velocity=0.0,
    stationary_time=0,
    duration=1,
    hold_after=float(1),
    stim_name="gray_ellipse",
    ))

for angle in range(0,361,30):
    stim.append(stimulus_details.MonocularStimulusDetails(
    texture=ellipse3,
    angle=angle,
    velocity=0.0,
    stationary_time=0,
    duration=1,
    hold_after=float(1),
    stim_name="gray_ellipse",
    ))

for angle in range(0,361,30):
    stim.append(stimulus_details.MonocularStimulusDetails(
    texture=ellipse3,
    angle=angle,
    velocity=0.0,
    stationary_time=0,
    duration=1,
    hold_after=float(1),
    stim_name="gray_ellipse",
    ))

for angle in range(0,361,30):
    stim.append(stimulus_details.MonocularStimulusDetails(
    texture=ellipse4,
    angle=angle,
    velocity=0.0,
    stationary_time=0,
    duration=1,
    hold_after=float(1),
    stim_name="gray_ellipse",
    ))

for angle in range(0,361,30):
    stim.append(stimulus_details.MonocularStimulusDetails(
    texture=rect1,
    angle=angle,
    velocity=0.0,
    stationary_time=0,
    duration=1,
    hold_after=float(1),
    stim_name="gray_ellipse",
    ))

for angle in range(0,361,30):
    stim.append(stimulus_details.MonocularStimulusDetails(
    texture=rect2,
    angle=angle,
    velocity=0.0,
    stationary_time=0,
    duration=1,
    hold_after=float(1),
    stim_name="gray_ellipse",
    ))

all_stimulus = stim
pstim = stimulus.OpenLoopStimulus(all_stimulus)

pstim.run()
