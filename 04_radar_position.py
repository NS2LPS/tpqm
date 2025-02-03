from qm.qua import *
from configuration_radar import qm, pulse_len, time_of_flight
from live_plot import LivePlotWindow

from qualang_tools.loops import from_array
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import numpy as np

###################
# The QUA program #
###################
f_min = 500 * u.MHz
df = -8 * u.MHz
n_points_position = 126
n_zero_padding = 124
frequencies = f_min + np.arange(n_points_position)*df  

with program() as prog:
    n = declare(int)  # QUA variable for the averaging loop
    f = declare(int)  # QUA variable for the readout frequency
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'
    

    with infinite_loop_():
        with for_(*from_array(f, frequencies)):  # QUA for_ loop for sweeping the frequency
            # Update the frequency of the digital oscillator linked to the resonator element
            update_frequency("radar", f)
            measure(
                "pulse",
                "radar",
                None,
                dual_demod.full("cos", "sin", I),
                dual_demod.full("minus_sin", "cos", Q),
            )
            # Save the 'I' & 'Q' quadratures to their respective streams
            save(I, I_st)
            save(Q, Q_st)

    with stream_processing():
        # Cast the data into a 1D vector and store the results on the OPX processor
        I_st.buffer(n_points_position).zip(Q_st.buffer(n_points_position)).save("IQ")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots(2,1)
        # Plot
        self.xaxis = np.fft.fftshift(np.fft.fftfreq(n_points_position+n_zero_padding, d=-df))*3e8/2
        self.fftplot = self.ax[0].plot(self.xaxis, np.ones(n_points_position+n_zero_padding))[0]
        self.ax[0].set_xlabel('Position (m)')
        self.ax[1].set_ylabel('Position (m)')
        self.positions = []
        self.delay = 0.0

        
    def polldata(self):
        # Fetch the raw ADC traces 
        IQ = self.job.result_handles.get("IQ").fetch(1)
        if IQ is None:
            return        
        I = IQ['value_0']
        Q = IQ['value_1']
        S = I + 1j*Q
        S = S * np.exp(-1j*self.delay*2*np.pi*frequencies)
        M = np.abs(np.fft.fft(np.r_[S, np.zeros(n_zero_padding)]))
        M = np.fft.fftshift(M)
        self.positions.append(self.xaxis[np.argmax(M)])
        self.fftplot.set_ydata(M)        
        self.ax[0].set_ylim(0, np.max(M))
        self.ax[1].cla()
        self.ax[1].plot(self.positions)
        self.canvas.draw()
        
        

#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
window.show()
