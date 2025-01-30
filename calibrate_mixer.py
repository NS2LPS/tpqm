# Run this file to calibrate the mixer
# Then, restart the QM with 'run -i configuration' 

from configuration_spectro import rf1_LO, rf1_IF, qm

caldict = {rf1_LO: [rf1_IF,]}

print('Calibrating ...')
qm.calibrate_element('rf1',caldict)
print('Done')    
