# Use 'run -i calibrate_mixer' to calibrate the mixer
# Then, restart the QM with 'run -i reload' 

from configuration import radar_LO, radar_IF, qm

caldict = {radar_LO: [radar_IF,]}

print('Calibrating ...')
qm.calibrate_element('radar',caldict)
print('Done')    
