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
# The frequency sweep parameters
f_min = 100 * u.MHz
f_max = 300 * u.MHz
df = 100 * u.kHz
frequencies = np.arange(f_min, f_max + 0.1, df)  # The frequency vector (+ 0.1 to add f_max to frequencies)

with program() as prog:
    n = declare(int)  # QUA variable for the averaging loop
    f = declare(int)  # QUA variable for the readout frequency
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'
    
    with infinite_loop_():
        play("pulse" * amp(IO1), "rf1")

    with infinite_loop_():
        with for_(*from_array(f, frequencies)):  # QUA for_ loop for sweeping the frequency
            # Update the frequency of the digital oscillator linked to the resonator element
            update_frequency("spectro", f)
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
        I_st.buffer(len(frequencies)).save("I")
        Q_st.buffer(len(frequencies)).save("Q")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots()
        # Plot
        self.spectrum = self.ax.plot((spectro_LO + frequencies)/1e6,np.ones(len(frequencies)))[0]
        self.ax.set_xlabel('Frequency (MHz)')
        self.ax.set_ylabel('Signal (dB)')
        self.ax.set_ylim(-120,-10)
        
    def polldata(self):
        # Fetch the raw ADC traces and convert them into Volts
        I = self.job.result_handles.get("I").fetch(1)
        Q = self.job.result_handles.get("Q").fetch(1)
        if I is None or Q is None:
            return
        self.spectrum.set_ydata(10*np.log10(I**2+Q**2))
        self.canvas.draw()

#######################
# Execute the program #
#######################
job = qm.execute(prog)
qm.set_io1_value(1.0)
window = myLivePlot(job)
window.show()
