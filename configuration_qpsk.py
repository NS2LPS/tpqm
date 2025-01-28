"""
QUA-Config supporting OPX+ & Octave
"""

from qm import QuantumMachinesManager
import os
from qualang_tools.units import unit
import numpy as np

#######################
# AUXILIARY FUNCTIONS #
#######################
u = unit(coerce_to_integer=True)


######################
# Network parameters #
######################
from qp_ip import qop_ip
cluster_name = "Cluster_1"  # Write your cluster_name if version >= QOP220
qop_port = None  # Write the QOP port if version < QOP220


#############################################
#                Radar                      #
#############################################
main_LO = 7.0 * u.GHz
carrier_IF = 250 * u.MHz
tx_IF = 125 * u.MHz

# Time of flight
time_of_flight = 216

# Pulse length
readout_pulse_len = 16 * u.ns

msg=np.load("msg.npz")
msgI=np.kron(msg["x"],np.ones(64))
msgQ=np.kron(msg["y"],np.ones(64))

# Pulse length
pulse_len = len(msg)
pulse_amp = 0.1

#############################################
#                  Config                   #
#############################################
config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                1: {"offset": 0.0},  # I RF1
                2: {"offset": 0.0},  # Q RF1
                3: {"offset": 0.0},  # I RF2
                4: {"offset": 0.0},  # Q RF2
            },
            "digital_outputs": {},
            "analog_inputs": {
                1: {"offset": 0.009342, "gain_db": -6},  # I from down-conversion
                2: {"offset": 0.003681, "gain_db": -6},  # Q from down-conversion
            },
        },
    },
    "elements": {
        "carrier": {
            "RF_inputs": {"port": ("oct1", 1)},
            "RF_outputs": {"port": ("oct1", 1)},
            "intermediate_frequency": carrier_IF,
            "operations": {
                "cw": "pulse",
                "cw": "message",
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
        "emitter": {
            "RF_inputs": {"port": ("oct1", 1)},
            "RF_outputs": {"port": ("oct1", 1)},
            "intermediate_frequency": tx_IF,
            "operations": {
                "cw": "pulse",
                "cw": "message",
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
        "phaselock": {
            "RF_inputs": {"port": ("oct1", 2)},
            "RF_outputs": {"port": ("oct1", 2)},
            "intermediate_frequency": carrier_IF,
            "operations": {
                "readout": "readout_pulse",
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
        "receiver": {
            "RF_inputs": {"port": ("oct1", 2)},
            "RF_outputs": {"port": ("oct1", 2)},
            "intermediate_frequency": tx_IF,
            "operations": {
                "readout": "readout_pulse",
            },
            "time_of_flight": time_of_flight,
            "smearing": 0,
        },
    },
    "octaves": {
        "oct1": {
            "RF_outputs": {
                1: {
                    "LO_frequency": main_LO,
                    "LO_source": "internal",
                    "output_mode": "always_on",
                    "gain": 0,
                },
                2: {
                    "LO_frequency": main_LO,
                    "LO_source": "external",
                    "output_mode": "always_on",
                    "gain": 0,
                },
            },
            "RF_inputs": {
                1: {
                    "LO_frequency": main_LO,
                    "LO_source": "internal",
                },
            },
            "RF_inputs": {
                2: {
                    "LO_frequency": main_LO,
                    "LO_source": "internal",
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
        "message": {
            "operation": "control",
            "length": len(msgI),
            "waveforms": {
                "I": "message_I",
                "Q": "message_Q",
            },            
        },
        "readout_pulse": {
            "operation": "measurement",
            "length": readout_pulse_len,
            "waveforms": {
                "I": "zero_wf",
                "Q": "zero_wf",
            },
            "integration_weights": {
                "cos": "cosine_weights",
                "sin": "sine_weights",
                "minus_sin": "minus_sine_weights",
            },
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "const_wf": {"type": "constant", "sample": pulse_amp},
        "zero_wf": {"type": "constant", "sample": 0.0},
        "message_I": {"type": "arbitrary", "samples": msgI},
        "message_Q": {"type": "arbitrary", "samples": msgQ},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 0)]},
    },
    "integration_weights": {
        "cosine_weights": {
            "cosine": [(1.0, readout_pulse_len)],
            "sine": [(0.0, readout_pulse_len)],
        },
        "sine_weights": {
            "cosine": [(0.0, readout_pulse_len)],
            "sine": [(1.0, readout_pulse_len)],
        },
        "minus_sine_weights": {
            "cosine": [(0.0, readout_pulse_len)],
            "sine": [(-1.0, readout_pulse_len)],
        },
    },
}


#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name, log_level="ERROR", octave_calibration_db_path=os.getcwd()) 
qm = qmm.open_qm(config)
