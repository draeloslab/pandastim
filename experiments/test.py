from pandastim import stimuli, textures
import pandas as pd


save_path = None

df = pd.read_hdf(r'C:\Soft_Kitty\Anaconda3\envs\clean_pstim\Lib\site-packages\pandastim\experiments\imaging.hdf')
df.loc[:, 'texture_0'] = textures.GratingGrayTexXY(texture_size=(1024,1024), spatial_frequency=60)
df.loc[:, 'texture_1'] = textures.GratingGrayTexXY(texture_size=(1024,1024), spatial_frequency=60)
df.loc[:, 'duration'] = df.duration.values + df.stationary_time.values

stims = stimuli.OpenLoopStimulus(df)
stims.run()