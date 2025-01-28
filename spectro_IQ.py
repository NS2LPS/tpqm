from qm.qua import *
from configuration_spectro import qm, spectro_LO
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
    n = declare(int)  # QUA variable for the averaging loop
    f = declare(int)  # QUA variable for the readout frequency
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'
    
    with infinite_loop_():
        #play('pulse_name'*  amp(v_00, v_01, v_10, v_11), 'element'),
        play("pulse" * amp(1.0,0.0,0.0,1.0), "radar")
        play("pulse" * amp(0.0,-1.0,1.0,0.0), "radar")
        play("pulse" * amp(-1.0,1.0,0.0,-1.0), "radar")
        play("pulse" * amp(0.0,1.0,-1.0,0.0), "radar")

    with infinite_loop_():
        with for_(n, 0, n < n_points, n + 1):  # QUA for_ loop for averaging
            # Send a readout pulse and demodulate the signals to get the 'I' & 'Q' quadratures)
            measure(
                "readout",
                "spectro",
                None,
                dual_demod.full("cos", "sin", I),
                dual_demod.full("minus_sin", "cos", Q),
            )
            # Save the 'I' & 'Q' quadratures to their respective streams
            save(I, I_st)
            save(Q, Q_st)

    with stream_processing():
        # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
        I_st.buffer(n_points).save("I")
        Q_st.buffer(n_points).save("Q")

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
        self.ax.set_xlim(-0.3,0.3)
        self.ax.set_ylim(-0.3,0.3)
        self.ax.set_aspect('equal')
        
    def polldata(self):
        # Fetch the raw ADC traces and convert them into Volts
        I = self.job.result_handles.get("I").fetch(1)
        Q = self.job.result_handles.get("Q").fetch(1)
        self.spectrum.set_xdata(I)
        self.spectrum.set_ydata(Q)
        self.canvas.draw()

#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
window.show()