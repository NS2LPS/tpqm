from qm.qua import *
from configuration import qm
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)


###################
# The QUA program #
###################
with program() as prog:
    with infinite_loop_():
        play("pulse", "rf1")
        wait(10*u.us)


#######################
# Execute the program #
#######################
job = qm.execute(prog)
