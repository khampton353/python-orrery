''' builder.py
    A utility that batches the creation of binary orbit files. It uses the data
    strings in 'planet_config' to get the filename arguments needed by 
    buildorbit.py. It expects the Ephemeris file for the planet to be the 
    second item in the colon-seperated configuration string.
    It currently does not collect error codes.
'''
''' Changes
    01/31/2018
    -Deleted commented-out code
'''
   
import os

pdata = []
os.makedirs('bin', exist_ok=True)
with open('config/planet_config', 'r') as cf:
    pdata = list(cf)


for lne in pdata:
    if lne[0] == '#':
        continue
    if lne[0] == '$':
        break
    os.system('python3 buildorbit.py {}'.format(lne.split(':')[1]))


