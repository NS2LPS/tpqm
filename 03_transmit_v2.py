from qm.qua import *
from configuration_transmit import qm

from live_plot import LivePlotWindow

from qualang_tools.loops import from_array
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import numpy as np

###################
# The QUA program #
###################
n_points=4096

msg=np.load("msg_1007.npz")
msgI=msg["x"]
msgQ=msg["y"]

with program() as prog:
    m = declare(int)
    Im = declare(fixed,value=msgI)
    Qm = declare(fixed,value=msgQ)    
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'
    Il = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Ql = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    Il_st = declare_stream()  # Stream for the 'I' quadrature
    Ql_st = declare_stream()  # Stream for the 'Q' quadrature
    
    with infinite_loop_():
        with for_(m, 0, m < len(msgI), m + 1):  # QUA for_ loop for averaging
            play("pulse" * amp(Im[m],0.,0.,Qm[m]),"emitter")
            play("pulse","carrier_emitter")

    with infinite_loop_():
        # Send a readout pulse and demodulate the signals to get the 'I' & 'Q' quadratures)
        measure(
            "readout",
            "receiver",
            None,
            dual_demod.full("cos", "sin", I),
            dual_demod.full("minus_sin", "cos", Q),
        )
        measure(
            "readout",
            "carrier_receiver",
            None,
            dual_demod.full("cos", "sin", Il),
            dual_demod.full("minus_sin", "cos", Ql),
        )
        # Save the 'I' & 'Q' quadratures to their respective streams
        save(I, I_st)
        save(Q, Q_st)
        save(Il, Il_st)
        save(Ql, Ql_st)

    with stream_processing():
        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
        I_st.buffer(n_points).zip(Q_st.buffer(n_points)).zip(Il_st.buffer(n_points)).zip(Ql_st.buffer(n_points)).save("IQ")


####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots()
        # Plot
        self.IQplot = self.ax.plot(np.ones(n_points),np.ones(n_points),',')[0]
        self.ax.set_xlabel('I')
        self.ax.set_ylabel('Q')
        self.rmax = 0
        self.ax.set_aspect('equal')
        
    def polldata(self):
        IQ = self.job.result_handles.get("IQ").fetch(1)
        if IQ is None:
            return        
        I = IQ['value_0']
        Q = IQ['value_1']        
        Il = IQ['value_2']
        Ql = IQ['value_3']
        a = np.angle(Il+1j*Ql)
        S = (I+1j*Q)*np.exp(-1j*a)
        self.IQplot.set_xdata(S.real)
        self.IQplot.set_ydata(S.imag)
        # Autoscale axis
        rmax = np.max(np.abs(S))*1.1
        if rmax>self.rmax:
            self.rmax = rmax
            self.ax.set_xlim(-rmax,rmax)
            self.ax.set_ylim(-rmax,rmax)            
        self.canvas.draw()

#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
window.show()
