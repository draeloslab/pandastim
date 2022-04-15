from pandastim import stimuli, textures
import pandas as pd


save_path = None

# df = pd.read_hdf(r'C:\Soft_Kitty\Anaconda3\envs\clean_pstim\Lib\site-packages\pandastim\experiments\imaging.hdf')

df = pd.read_hdf(r'D:\autumnal_luzps_no_tex.hdf')

df = df.loc[1:]

df.loc[:, 'texture_0'] = textures.GratingGrayTexXY(texture_size=(1024,1024), spatial_frequency=60)
df.loc[:, 'texture_1'] = textures.GratingGrayTexXY(texture_size=(1024,1024), spatial_frequency=60)

df.loc[:, 'stationary_time'] = df.stat_time.values
# df.loc[:, 'duration'] = df.duration.values + df.stationary_time.values

df = pd.concat([df] * 10)
df.reset_index(inplace=True)

stims = stimuli.OpenLoopStimulus(df)
stims.run()
