"""
pandastim/examples/open_loop.py

example chaining our two previous examples together and adding binocular stimuli

-a gray sinusoidal texture, set into a moving gray stimulus

-a red sinusoidal texture, set into a moving red stimulus

-a list of these stimuli can be put into an openloop stimulus sequencingOpenLoo stimuli class

-a showbase instance that moves the stimulus according to the stimulusDetails parameters of each

Part of pandastim package: https://github.com/mattdloring/pandastim
"""
from pandastim import utils
from pandastim.stimuli import stimulus, stimulus_details, textures

# create a texture
sin_gray_tex = textures.SinGrayTex(
    texture_size=1024,
    frequency=32,
)
# create a wholefield stimulus with that texture
sin_gray_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=sin_gray_tex,
    angle=180,
    velocity=0.05,
    stationary_time=2,
    duration=24,
    hold_after=12.0,
    stim_name="moving_gray",
)
# create a different texture
sin_red_tex = textures.SinRgbTex(texture_size=1024, frequency=30, color=(255, 0, 0))
# different wholefield stimulus
sin_red_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=sin_red_tex,
    angle=90,
    velocity=-0.05,
    stationary_time=5,
    duration=20,
    hold_after=float(9),
    stim_name="red_sin",
)

# circle_tex= textures.CircleGrayTex(
#     texture_size = 3000, 
#     num_circles = 1,
#     circle_center= (1100,1800),
#     circle_radius= 10,
#     texture_name='gray_circle',
#     bg_intensity= 200,
#     fg_intensity=50,
# )

# circle_tex= textures.CircleGrayTex(
#     texture_size = 5000, 
#     frequency = 200,
#     circle_center= (2600,3000),
#     circle_radius= 20,
#     spacing= 100,
#     texture_name='gray_circle',
#     bg_intensity= 200,
#     fg_intensity=50,
# )
# circle_stimulus = stimulus_details.MonocularStimulusDetails(
#     texture=circle_tex,
#     angle=90,
#     velocity=0.05,
#     stationary_time=0,
#     duration=5,
#     hold_after=float(5),
#     stim_name="gray_circ",
# )

# ellipse_tex= textures.EllipseGrayTex(
#     texture_size = 5000, 
#     frequency = 1,
#     center= (2750,3000),
#     h_radius= 40,
#     v_radius= 20,
#     texture_name='gray_ellipse',
#     bg_intensity= 200,
#     fg_intensity=50,
# )

ellipse_tex= textures.EllipseGrayTex(
    texture_size = 1600, 
    frequency = 100,
    center= (865,955),
    width= 50,
    length= 800,
    texture_name='gray_ellipse',
    bg_intensity= 200,
    fg_intensity=50,
)
ellipse_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=ellipse_tex,
    angle=90,
    velocity=0.05,
    stationary_time=0,
    duration=5,
    hold_after=float(5),
    stim_name="gray_ellipse",
)

rect_tex= textures.RectGrayTex(
    texture_size = 1600, 
    frequency = 200,
    center= (865,955),
    length= 85,
    width= 2000,
    texture_name='gray_rectangle',
    bg_intensity= 200,
    fg_intensity=50,
)
rect_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=rect_tex,
    angle=90,
    velocity=0.08,
    stationary_time=0,
    duration=5,
    hold_after=float(5),
    stim_name="gray_rectangle",
)


# We can create binocular by combining monocular
combined_binoc_stim = stimulus_details.monocular2binocular(
    sin_gray_stimulus, sin_red_stimulus
)

# or from scratch
grate_gray_tex = textures.GratingGrayTex(texture_size=1024, frequency=32)
grate_gray_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=grate_gray_tex,
    angle=90,
    velocity=0.05,
    stationary_time=2,
    duration=24,
    hold_after=12.0,
    stim_name="moving_gray",
)


fresh_binoc_stim = stimulus_details.BinocularStimulusDetails(
    stim_name="wholefield_right",
    angle=(90, 90),
    velocity=(0.1, 0.1),
    duration=(20, 20),
    stationary_time=(10, 10),
    hold_after=(9.0, 9.0),
    texture=(sin_gray_tex, grate_gray_tex),
)

# callibration_text = textures.CallibrationDots(
#     texture_size = 1600,
#     circle_center= (865,955),
#     circle_radius= 25,
#     bg_intensity=200,
#     texture_name='callibration_dots',
# )
# callibration_stim = stimulus_details.MonocularStimulusDetails(
#     texture=callibration_text,
#     angle=90,
#     velocity=0.0,
#     stationary_time=0,
#     duration=60,                                    
#     hold_after=float(60),
#     stim_name="callibration_dots",
# )
           
all_stimuli = [rect_stimulus]
#[circle_stimulus, ellipse_stimulus]


pstim = stimulus.OpenLoopStimulus(all_stimuli)

pstim.run()

#%%
