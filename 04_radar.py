from qm.qua import *
from configuration_radar import qm, time_of_flight
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
n_points = 126
frequencies = f_min + np.arange(n_points)*df  


with program() as prog:
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
        I_st.buffer(n_points).zip(Q_st.buffer(n_points)).save("IQ")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots()
        # Plot
        self.IQplot = self.ax.plot(np.ones(n_points), np.ones(n_points),'.')[0]
        self.ax.set_xlabel('I')
        self.ax.set_ylabel('Q')
        self.rmax = 0.0
        self.delay = 0.0
        self.ax.set_aspect('equal')
        self.canvas.figure.tight_layout()
        
    def polldata(self):
        # Fetch the raw ADC traces
        IQ = self.job.result_handles.get("IQ").fetch(1)
        if IQ is None:
            return        
        I = IQ['value_0']
        Q = IQ['value_1']
        S = I + 1j*Q
        S = S * np.exp(-1j*self.delay*2*np.pi*frequencies)
        self.S = np.copy(S)
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
