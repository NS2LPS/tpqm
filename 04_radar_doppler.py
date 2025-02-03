from qm.qua import *
from configuration_radar import qm, pulse_len, radar_LO
from live_plot import LivePlotWindow

from qualang_tools.loops import from_array
from qualang_tools.units import unit
u = unit(coerce_to_integer=True)
import numpy as np

###################
# The QUA program #
###################
n_points_velocity = 128

with program() as prog:
    n = declare(int)  # QUA variable for the averaging loop
    f = declare(int)  # QUA variable for the readout frequency
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'
    

    with infinite_loop_():
        measure(
            "readout",
            "radar",
            None,
            dual_demod.full("cos", "sin", I),
            dual_demod.full("minus_sin", "cos", Q),
        )
        wait(1*u.ms - pulse_len*u.ns)
        # Save the 'I' & 'Q' quadratures to their respective streams
        save(I, I_st)
        save(Q, Q_st)

    with stream_processing():
        # Cast the data into a 1D vector and store the results on the OPX processor
        I_st.buffer(n_points_velocity).zip(Q_st.buffer(n_points_velocity)).save("IQ")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots(2,1)
        # Plot
        self.xaxis = np.fft.fftshift(np.fft.fftfreq(n_points_velocity, d=1e-3))*3e8/2/radar_LO
        self.fftplot = self.ax[0].plot(self.xaxis, np.ones(n_points_velocity))[0]
        self.ax[0].set_xlabel('Velocity (m/s)')
        self.ax[1].set_ylabel('Velocity (m/s)')
        self.velocities = []

        
    def polldata(self):
        # Fetch the raw ADC traces 
        IQ = self.job.result_handles.get("IQ").fetch(1)
        if IQ is None:
            return        
        I = IQ['value_0']
        Q = IQ['value_1']
        S = I+1j*Q
        M = np.abs(np.fft.fft(S))
        M[0] = np.nan
        #M[-1] = np.nan
        M = np.fft.fftshift(M)
        self.velocities.append(self.xaxis[np.nanargmax(M)])
        self.fftplot.set_ydata(M)        
        self.ax[0].set_ylim(0, np.nanmax(M))
        self.ax[1].cla()
        self.ax[1].plot(self.velocities)
        self.canvas.draw()
        
        

#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
window.show()
