from qm.qua import *
from configuration import qm



###################
# The QUA program #
###################
with program() as prog:
    with infinite_loop_():
        play("pulse", "rf1")


#######################
# Execute the program #
#######################
job = qm.execute(prog)
