from qm.qua import *
from configuration_qpsk import qm
from live_plot import LivePlotWindow

from qualang_tools.loops import from_array
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import numpy as np

###################
# The QUA program #
###################
n_points=16384

with program() as prog:
    n = declare(int)  # QUA variable for the averaging loop
    f = declare(int)  # QUA variable for the readout frequency
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
        play("message","emitter")
        play("pulse","carrier")

    with infinite_loop_():
        with for_(n, 0, n < n_points, n + 1):  # QUA for_ loop for averaging
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
                "phaselock",
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
        I_st.buffer(n_points).save("I")
        Q_st.buffer(n_points).save("Q")
        Il_st.buffer(n_points).save("Il")
        Ql_st.buffer(n_points).save("Ql")

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
        self.ax.set_xlim(-0.003,0.003)
        self.ax.set_ylim(-0.003,0.003)
        self.ax.set_aspect('equal')
        self.rot_angle = -12.+180
        
    def polldata(self):
        I = self.job.result_handles.get("I").fetch(1)
        Q = self.job.result_handles.get("Q").fetch(1)
        Il = self.job.result_handles.get("Il").fetch(1)
        Ql = self.job.result_handles.get("Ql").fetch(1)
        a = self.rot_angle/180*np.pi - np.angle(Il+1j*Ql)
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
window.show()