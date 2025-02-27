#! /usr/bin/python3

from pyaudio import PyAudio
import time

filename = 'tt'


framerate = 41900
p= PyAudio()
stream = p.open(format=p.get_format_from_width(1), # open stream
                    channels=1,
                    rate=framerate,
                    output=True)

# from stackoverflwo
def square_wave(freq, duration, volume, framerate):
    total=int(round(framerate*(duration/1000))) # calculate length of audio in samples
    i=0 # played samples counter
    sample_threshold=int(round(framerate*(0.5/freq))) # how much frames to do silence/sound (the frequence delay in samples)
    samples_last=0 # played samples counter (resets each sample_threshold)
    value=int(round(volume*255)) # the value to yield
    while i<=total : # play until the sound ends
        yield value # yield the value
        samples_last+=1 # count played sample
        if samples_last>=sample_threshold : # if played samples reach the threshold...
            samples_last=0 # reset counter
            value=0 if value!=0 else int(round(volume*255)) # switch value to volume or back to 0
        i+=1 # total counter increment

def playtone(freq, duration, volume):
    volume /= 100  # convert to 0-1
    duration = duration / 1000
    #data = tuple(square_wave(freq, 1000, volume, framerate))
    print("freq", freq, 'dur=', duration)
    data = tuple(square_wave(freq, duration, volume, framerate))
    stream.write(bytes(bytearray(data)))

fin = open(filename, "r")
db = []
for line in fin.readlines():
    print('line = ', line)
    
    tokens = line.split()
    print("toekns=", tokens)
    
    if tokens[0] != 'music':
        continue
    
    freq = float(tokens[4])
    timestamp = float(tokens[6])
    
    print(freq, timestamp)
    db.append([freq, timestamp])
    
for i in range(len(db)-1):
    freq = db[i][0]
    ts = db[i][1]
    ts1 = db[i+1][1]
    duration = ts1 - ts
    playtone(freq, duration, 100)

stream.close()
    

