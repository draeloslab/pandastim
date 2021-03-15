"""
pandastim/utils.py
Helper functions used in multiple classes in stimulu/textures

Part of pandastim package: https://github.com/EricThomson/pandastim
"""
import numpy as np
import threading
import zmq
import time
import os

from direct.showbase import DirectObject
from direct.showbase.MessengerGlobal import messenger

from scipy import signal
from datetime import datetime as dt

def port_provider():
    """
    returns a random free port on PC
    """
    c = zmq.Context()
    s = c.socket(zmq.SUB)
    rand_port = s.bind_to_random_port('tcp://*', min_port=5000, max_port=8000, max_tries=100)
    c.destroy()
    return rand_port

def updated_saving(file_path, fish_id, fish_age):
    """
    Initializes saving: saves texture classes and params for
    input-coupled stimulus classes.

    Updated from earlier -- dont remember why different
    """
    if '\\' in file_path:
        file_path = file_path.replace('\\', '/')

    val_offset = 0
    newpath = file_path
    while os.path.exists(newpath):
        val_offset += 1
        newpath = file_path[:file_path.rfind('/') + 1] + file_path[
                                                                   file_path.rfind('/') + 1:][:-4] \
                  + '_' + str(val_offset) + '.txt'

    file_path = newpath

    print(f"Saving data to {file_path}")
    filestream = open(file_path, "a")

    filestream.write(f"fish{fish_id}_{fish_age}dpf_{dt.now()}")
    filestream.flush()
    return filestream


def sin_byte(X, freq = 1):
    """
    Creates unsigned 8 bit representation of sin (T_unsigned_Byte). 
    """
    sin_float = np.sin(freq*X)
    sin_transformed = (sin_float + 1)*127.5; #from 0-255
    return np.uint8(sin_transformed)

def grating_byte(X, freq = 1):
    """
    Unsigned 8 bit representation of a grating (square wave)
    """
    grating_float = signal.square(X*freq)
    grating_transformed = (grating_float + 1)*127.5; #from 0-255
    return np.uint8(grating_transformed)

def save_initialize(file_path, tex_classes, stim_params):
    """
    Initializes saving: saves texture classes and params for 
    input-coupled stimulus classes.
    """
    print(f"Saving data to {file_path}")
    filestream = open(file_path, "a")
    for ind_tex, tex_class in enumerate(tex_classes):
        filestream.write(f"{ind_tex}: {tex_class} {stim_params[ind_tex]}\n")
        filestream.flush()
    filestream.write("\n")
    filestream.flush()
    return filestream
 
def card2uv(val):
    """ 
    from model (card) -based normalized device coordinates (-1,-1 bottom left, 1,1 top right)
    appropriate for cards to texture-based uv-coordinates. 
    
    For more on these different coordinate systems for textures:
        https://docs.panda3d.org/1.10/python/programming/texturing/simple-texturing
        
    """
    return 0.5*val

def uv2card(val):
    """
    Transform from texture-based uv-coordinates to card-based normalized device coordinates
    """
    return 2*val
    
    
class Publisher:
    """
    Publisher wrapper class for zmq.
    """
    def __init__(self, port = "1234"):
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(r"tcp://127.0.0.1:" + self.port)

    def kill(self):
        self.socket.close()
        self.context.term()
    
class Subscriber:
    """
    Subscriber wrapper class for zmq.
    Default topic is every topic (""). 
    """
    def __init__(self, port = "1234", topic = ""):
        self.port = port
        self.topic = topic
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(r"tcp://127.0.0.1:" + str(self.port))
        self.socket.subscribe(self.topic)
        
    def kill(self):
        self.socket.close()
        self.context.term() 
        
class Monitor(DirectObject.DirectObject):
    """
    Use a subscriber to continuously monitor publisher, and
    emit messages for the panda3d event handler.
    
    This is used for closed-loop stimuli.
    
    Matt: this is a working hack : see working/monitor_notes.txt.
    """
    def __init__(self, subscriber):
        self.sub = subscriber
        self.run_thread = threading.Thread(target = self.run)
        self.run_thread.daemon = True #let's you kill it
        self.run_thread.start()

    def run(self):     
        while True:
            data = self.sub.socket.recv() #recv_string()
            topic, message = data.split()
            #emit message for panda3d (convert from byte to string)
            messenger.send("stim" + str(message, 'utf-8'))

    def kill(self):
        self.run_thread.join()
        

class MonitorDataPass(DirectObject.DirectObject):
    """
    this monitor passes the data through to pandas
    """
    def __init__(self, subscriber):
        self.sub = subscriber

        self.run_thread = threading.Thread(target=self.run)

        self.run_thread.daemon = True
        self.run_thread.start()

    def run(self):
        # this is run on a separate thread so it can sit in a loop waiting to receive messages
        while True:
            topic = self.sub.socket.recv_string()
            data = self.sub.socket.recv_pyobj()
            # print(data)
            # this is a duplication at the moment, but provides an intermediate processing stage
            messenger.send('stimulus', [data])

    def kill(self):
        self.run_thread.join()

class Emitter(DirectObject.DirectObject):
    """
    Given three lists (x, y, theta): 
    emit the xytheta values in the list with period seconds betwween them, pause, and repeat.
    """
    def __init__(self, x_vals, y_vals, theta_vals, period = 0.2, pause = 1.0):
        self.x_vals = x_vals
        self.y_vals = y_vals
        self.theta_vals = theta_vals
        self.num_points = len(self.x_vals)
        assert(len(x_vals) == len(y_vals) == len(theta_vals)), "x y and theta must be same length"
        self.period = period
        self.pause = pause
        self.killed = False
        self.run_thread = threading.Thread(target = self.run)
        self.run_thread.daemon = True
        self.run_thread.start()
        
    def run(self):
        while True:
            for ind, (x_val, y_val, theta_val) in enumerate(zip(self.x_vals, self.y_vals, self.theta_vals)):
                #print(f"stim {x_val} {y_val} {theta_val}")
                messenger.send("stim", [x_val, y_val, theta_val])
                if ind == 0:
                    time.sleep(self.pause)
                else:
                    time.sleep(self.period)
            print(f"Emitter cycle done: pausing {self.pause} seconds.")
            time.sleep(self.pause)
             
    def kill(self):
        self.run_thread.join()


def sequence_runner(df, port="5005"):
    # this runs a dataframe of stimuli for you

    time.sleep(5)

    _context = zmq.Context()
    _socket = _context.socket(zmq.PUB)
    _socket.bind('tcp://*:' + str(port))
    stimulus_topic = 'stim'

    stim_n = 0

    current_length = df.loc[stim_n].duration + df.loc[stim_n].stationary_time
    t0 = time.time()

    _socket.send_string(stimulus_topic, zmq.SNDMORE)
    _socket.send_pyobj(df.loc[stim_n])

    while stim_n <= len(df) - 1:
        if time.time() - t0 <= current_length:
            pass
        else:
            stim_n += 1

            current_length = df.loc[stim_n].duration + df.loc[stim_n].stationary_time
            t0 = time.time()
            _socket.send_string(stimulus_topic, zmq.SNDMORE)
            _socket.send_pyobj(df.loc[stim_n])


        
#%%        
if __name__ == '__main__':
    to_test = 1
    if to_test == 0:
        # Monitor test: first turn on pub_class_toggle.py or pub_class_toggle3.py
        sub = Subscriber(topic = "stim")
        m = Monitor(sub)
        time.sleep(60)
        m.kill()
    elif to_test == 1:
        # Emitter test
        x = [.1, .2, .3, .4, .5]
        y = [.2, .2, .3, .4, .5]
        theta = [10, 15, 20, 25, 30]
        em = Emitter(x, y, theta, period = 1, pause = 2)
        time.sleep(4)
        em.kill()

    
    
    
    
    
    
    
    
    
    
