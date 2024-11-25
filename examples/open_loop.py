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

circle_tex= textures.CircleGrayTex(
    texture_size = 1024, 
    num_circles = 1000,
    circle_center= (450,100),
    circle_radius= 6,
    texture_name='gray_circle',
    bg_intensity= 200,
    fg_intensity=50,
)
circle_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=circle_tex,
    angle=90,
    velocity=0.2,
    stationary_time=0,
    duration=20,
    hold_after=float(20),
    stim_name="gray_circ",
)

ellipse_tex= textures.EllipseGrayTex(
    texture_size = 1024, 
    frequency = 1,
    center= (450,100),
    h_radius= 15,
    v_radius= 20,
    texture_name='gray_ellipse',
    bg_intensity= 200,
    fg_intensity=50,
)
ellipse_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=ellipse_tex,
    angle=90,
    velocity=0.1,
    stationary_time=0,
    duration=20,
    hold_after=float(20),
    stim_name="gray_circ",
)

rect_tex= textures.RectGrayTex(
    texture_size = 1024, 
    frequency = 1,
    center= (450,100),
    length= 100,
    width= 20,
    texture_name='gray_rectangle',
    bg_intensity= 200,
    fg_intensity=50,
)
rect_stimulus = stimulus_details.MonocularStimulusDetails(
    texture=rect_tex,
    angle=90,
    velocity=0.1,
    stationary_time=0,
    duration=20,
    hold_after=float(20),
    stim_name="gray_circ",
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

all_stimuli = [rect_stimulus]
    #[circle_stimulus]
    # multi_circle_stim]
#     sin_gray_stimulus,
#     sin_red_stimulus,
#     combined_binoc_stim,
#     fresh_binoc_stim,
# ]


pstim = stimulus.OpenLoopStimulus(all_stimuli)

pstim.run()

#%%
