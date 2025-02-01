"""
QUA-Config supporting OPX+ & Octave
"""

from qm import QuantumMachinesManager
import os
from qualang_tools.units import unit

#######################
# AUXILIARY FUNCTIONS #
#######################
u = unit(coerce_to_integer=True)


######################
# Network parameters #
######################
from qm_ip import qop_ip, cluster_name
qop_port = None  # Write the QOP port if version < QOP220

#############################################
#       Experimental Parameters             #
#############################################
rf1_LO = 10. * u.GHz
rf1_IF = 250. * u.MHz

# Pulse length
pulse_len = 20 * u.ns
pulse_amp = 0.1  # Keep this value between -0.125 and +0.125

# Time of flight
time_of_flight = 216


#############################################
#                  Config                   #
#############################################
config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                1: {"offset": 0.0},  # I 
                2: {"offset": 0.0},  # Q 
            },
            "digital_outputs": {},
            "analog_inputs": {
                1: {"offset": 0.009342, "gain_db": -6},  # I from down-conversion
                2: {"offset": 0.003681, "gain_db": -6},  # Q from down-conversion
            },
        },
    },
    "elements": {
        "rf1": {
            "RF_inputs": {"port": ("oct1", 1)},
            "RF_outputs": {"port": ("oct1", 1)},
            "intermediate_frequency": rf1_IF,
            "operations": {
                "cw": "pulse",
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
    },
    "octaves": {
        "oct1": {
            "RF_outputs": {
                1: {
                    "LO_frequency": rf1_LO,
                    "LO_source": "internal",
                    "output_mode": "always_on",
                    "gain": 0,
                },
            },
            "connectivity": "con1",
        },
    },
    "pulses": {
        "pulse": {
            "operation": "control",
            "length": pulse_len,
            "waveforms": {
                "I": "const_wf",
                "Q": "zero_wf",
            },
        },
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": pulse_amp},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
}


#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, log_level="ERROR", octave_calibration_db_path=os.getcwd()) 
qm = qmm.open_qm(config)
