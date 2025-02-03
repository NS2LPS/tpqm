from qm.qua import *
from configuration_radar import qm, radar_LO, pulse_len
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
n_zero_padding = 130
n_points_velocity = 64
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
                "readout",
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
        I_st.buffer(n_points_velocity,n_points_position).zip(Q_st.buffer(n_points_velocity,n_points_position)).save("IQ")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots()
        # Plot
        self.xaxis = np.fft.fftshift(np.fft.fftfreq(n_points_position+n_zero_padding, d=-df))*3e8/2
        self.yaxis = np.fft.fftshift(np.fft.fftfreq(n_points_velocity, d=1e-3))*3e8/2/radar_LO
        self.spectrum = self.ax.pcolormesh(self.xaxis,self.yaxis,np.ones((n_points_velocity, n_points_position+n_zero_padding)))
        self.ax.set_xlabel('Position (m)')
        self.ax.set_ylabel('Velocity (m/s)')
        self.canvas.figure.colorbar(self.spectrum, ax=self.ax)
        
        
    def polldata(self):
        # Fetch the raw ADC traces 
        IQ = self.job.result_handles.get("IQ").fetch(1)
        if IQ is None:
            return        
        I = IQ['value_0']
        Q = IQ['value_1']
        S = I + 1j*Q
        S = S * np.exp(-1j*self.delay*2*np.pi*frequencies)
        M = np.abs(np.fft.fft2(np.c_[S, np.zeros((n_points_velocity,n_zero_padding))]))
        M[0,0] = np.nan
        M = np.fft.fftshift(M)
        self.spectrum.set_data(M)
        self.spectrum.set_clim(0,np.nanmax(M))
        self.canvas.draw()

#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
window.show()
