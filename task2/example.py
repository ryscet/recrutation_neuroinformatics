
#!/usr/bin/env python
# encoding: utf-8

from load_data import data, mice, phases

# List of animals in experiment
print list(mice)

# experiment phases
print phases.sections()
# start, end of each phase (as Unix time - https://en.wikipedia.org/wiki/Unix_time)
for phase in phases.sections():
    print phases.gettime(phase)
    
# Visits of a mouse to the rooms during one phase can be accesed like that:
phase = 'PHASE 1 dark'
mouse = list(mice)[0]
data.unmask_data()
data.mask_data(*phases.gettime(phase))
# Because of masking only visits starting in the given phase are returned.
start_times = data.getstarttimes(mouse)
end_times = data.getendtimes(mouse)
room_numbers = data.getaddresses(mouse)

for st, en, room in zip(start_times, end_times, room_numbers):
    print "visit to room %d, starting %f, ending %f" %(room, st, en)

