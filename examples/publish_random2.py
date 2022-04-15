"""
pandastim/publish_random2.py
zeromq publisher that generates random sequence of zeroes and ones.
Useful for testing socket-based communication protocols.

Needs to be paired with a subscriber that monitors its output.

For example, see examples/input_switcher_tex.py.

Part of pandastim package: https://github.com/mattdloring/pandastim
"""

import time
import random

from pandastim.utils import Publisher as Pub


def randomPublish2(port="1234"):
    pub = Pub(port=port)
    print("Starting publisher loop to generate random outputs...")
    while True:
        delay_time = random.uniform(0.4, 2)  #.5 3
        output = random.randint(0, 1)
        topic = b"stim"
        msg = str(output).encode('ascii')
        data = topic + b" " + msg
        pub.socket.send(data)
        print(f"pub.py: sent data: {data}")
        time.sleep(delay_time)
