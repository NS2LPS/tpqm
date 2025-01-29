# Use 'run -i calibrate_mixer' to calibrate the mixer
# Then, restart the QM with 'run -i reload' 

from configuration import rf1_LO, rf1_IF, qm

caldict = {rf1_LO: [rf1_IF,]}

print('Calibrating ...')
qm.calibrate_element('radar',caldict)
print('Done')    
