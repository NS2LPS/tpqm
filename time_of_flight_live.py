from qm.qua import *
import importlib
import configuration
importlib.reload(configuration)
from configuration import qm
from live_plot import LivePlotWindow
from scipy.signal import savgol_filter


from qualang_tools.units import unit
u = unit(coerce_to_integer=True)

###################
# The QUA program #
###################
with program() as prog:
    adc_st = declare_stream(adc_trace=True)  # The stream to store the raw ADC trace

    with infinite_loop_():
        # Reset the phase of the digital oscillator associated to the resonator element. Needed to average the cosine signal.
        reset_if_phase("rf1")
        # Sends the readout pulse and stores the raw ADC traces in the stream called "adc_st"
        measure("readout", "rf1", adc_st)
        # Wait 
        wait(20 * u.ms, "rf1")

    with stream_processing():
        # Will save average:
        adc_st.input1().average().save("adc1")
        adc_st.input2().average().save("adc2")
        # Will save only last run:
        adc_st.input1().save("adc1_single_run")
        adc_st.input2().save("adc2_single_run")

####################
# Live plot        #
####################
class myLivePlot(LivePlotWindow):
    def create_axes(self):
        # Create plot axes
        self.ax = self.canvas.figure.subplots(2,1,sharex=True)        

    def polldata(self):
        # Fetch the raw ADC traces and convert them into Volts
        adc1 = self.job.result_handles.get("adc1").fetch(1)
        adc2 = self.job.result_handles.get("adc2").fetch(1)
        adc1_single_run = self.job.result_handles.get("adc1_single_run").fetch(1)
        adc2_single_run = self.job.result_handles.get("adc2_single_run").fetch(1)
        if adc1 is None or adc2 is None or adc1_single_run is None or adc2_single_run is None:
            return
        # Convert to V
        adc1 = u.raw2volts(adc1)
        adc2 = u.raw2volts(adc2)
        adc1_single_run = u.raw2volts(adc1_single_run)
        adc2_single_run = u.raw2volts(adc2_single_run))  
        # Filter the data to get the pulse arrival time
        adc1_unbiased = adc1 - np.mean(adc1)
        adc2_unbiased = adc2 - np.mean(adc2)
        signal = savgol_filter(np.abs(adc1_unbiased + 1j * adc2_unbiased), 11, 3)
        # Detect the arrival of the readout signal
        th = (np.mean(signal[:100]) + np.mean(signal[:-100])) / 2
        delay = np.where(signal > th)[0][0]
        delay = np.round(delay / 4) * 4  # Find the closest multiple integer of 4ns
        # Plot
        self.ax[0].cla()
        t = np.arange(len(adc1))
        self.ax[0].plot(t,adc1_single_run,t,adc2_single_run)
        self.ax[1].cla()
        self.ax[1].plot(t,adc1,t,adc2)
        self.ax[1].axvline(delay,color='k',linestyle='--')
        self.ax[1].set_xlabel('Time (ns)')
        self.ax[0].set_ylabel('ADC signal (V)')
        self.ax[1].set_ylabel('ADC signal (V)')        
        self.canvas.draw()
        self.summary = (np.mean(adc1),np.mean(adc2),delay)
        
    def closeEvent(self, event):
        print("Terminating QM job.")
        print(f"DC offset to add to I in the config: {-self.summary[0]:.6f} V")
        print(f"DC offset to add to Q in the config: {-self.summary[1]:.6f} V")
        print(f"Time Of Flight to add in the config: {self.summary[2]} ns")
        self.job.halt()
        self.timer.stop()
        
        
#######################
# Execute the program #
#######################
job = qm.execute(prog)
window = myLivePlot(job)
window.show()