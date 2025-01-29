from qm.qua import *
import importlib
import configuration_qpsk
importlib.reload(configuration_qpsk)
from configuration_qpsk import qm

from live_plot import LivePlotWindow

from qualang_tools.loops import from_array
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import numpy as np

###################
# The QUA program #
###################
n_points=2048

msg=np.load("msg_1007.npz")
msgI=msg["x"]
msgQ=msg["y"]

with program() as prog:
    n = declare(int)  # QUA variable for the averaging loop
    m = declare(int)
    Im = declare(fixed,value=msgI)
    Qm = declare(fixed,value=msgQ)    
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    
    with infinite_loop_():
        with for_(m, 0, m < len(msgI), m + 1):  
            play("pulse" * amp(Im[m],0.,0.,Qm[m]),"emitter")

    with infinite_loop_():
        with for_(n, 0, n < n_points, n + 1):  
            # Demodulate the signals to get the 'I' & 'Q' quadratures)
            measure(
                "readout",
                "receiver",
                None,
                dual_demod.full("cos", "sin", I),
                dual_demod.full("minus_sin", "cos", Q),
            )
            # Save the 'I' & 'Q' quadratures to their respective streams
            save(I, I_st)
            save(Q, Q_st)

    with stream_processing():
        # Cast the data into a 1D vector and store the results on the OPX processor
        I_st.buffer(n_points).zip(Q_st.buffer(n_points)).save("IQ")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots()
        # Plot
        self.spectrum = self.ax.plot(np.ones(n_points),np.ones(n_points),',')[0]
        self.ax.set_xlabel('I')
        self.ax.set_ylabel('Q')
        self.ax.set_xlim(-0.3,0.3)
        self.ax.set_ylim(-0.3,0.3)
        self.ax.set_aspect('equal')
        self.rot_angle = 0.
        
    def polldata(self):
        IQ = self.job.result_handles.get("IQ").fetch(1)
        if IQ is None:
            return        
        I = IQ['value_0']
        Q = IQ['value_1']
        a = self.rot_angle/180*np.pi
        Ir = np.cos(a)*I-np.sin(a)*Q
        Qr = np.sin(a)*I+np.cos(a)*Q
        self.spectrum.set_xdata(Ir)
        self.spectrum.set_ydata(Qr)
        self.canvas.draw()

#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
qm.set_io1_value(1.0)
window.show()