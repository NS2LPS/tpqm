from qm.qua import *
from configuration import qm



###################
# The QUA program #
###################
with program() as prog:
    with infinite_loop_():
        play("pulse", "rf1")
        wait(2)
        play("pulse", "rf1")
        wait(1000)


#######################
# Execute the program #
#######################
job = qm.execute(prog)
