from qm.qua import *
from configuration_view_IQ import qm
from live_plot import LivePlotWindow

from qualang_tools.loops import from_array
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import numpy as np

###################
# The QUA program #
###################
n_points = 1024

with program() as prog:
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    
    with infinite_loop_():
        play("pulse", "emitter")

    with infinite_loop_():
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
        # Cast the data into a 1D vector, and store the results on the OPX processor
        I_st.buffer(n_points).zip(Q_st.buffer(n_points)).save("IQ")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots()
        # Plot
        self.spectrum = self.ax.plot(np.ones(n_points),np.ones(n_points),'.')[0]
        self.ax.set_xlabel('I')
        self.ax.set_ylabel('Q')
        self.ax.set_xlim(-0.5,0.5)
        self.ax.set_ylim(-0.5,0.5)
        self.ax.set_aspect('equal')
        
    def polldata(self):
        # Fetch the raw ADC traces
        IQ = self.job.result_handles.get("IQ").fetch(1)
        if IQ is None:
            return        
        I = IQ['value_0']
        Q = IQ['value_1']
        self.spectrum.set_xdata(I)
        self.spectrum.set_ydata(Q)
        self.canvas.draw()

#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
window.show()
