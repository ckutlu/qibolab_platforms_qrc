import pathlib

import networkx as nx
import yaml
from qibolab.channels import Channel, ChannelMap
from qibolab.instruments.qblox.cluster import (
    Cluster,
    Cluster_Settings,
    ReferenceClockSource,
)
from qibolab.instruments.qblox.cluster_qcm_bb import (
    ClusterQCM_BB,
    ClusterQCM_BB_Settings,
)
from qibolab.instruments.qblox.cluster_qcm_rf import (
    ClusterQCM_RF,
    ClusterQCM_RF_Settings,
)
from qibolab.instruments.qblox.cluster_qrm_rf import (
    ClusterQRM_RF,
    ClusterQRM_RF_Settings,
)
from qibolab.instruments.qblox.controller import QbloxController
from qibolab.instruments.qblox.port import (
    ClusterBB_OutputPort_Settings,
    ClusterRF_OutputPort_Settings,
    QbloxInputPort_Settings,
)
from qibolab.instruments.rohde_schwarz import SGS100A
from qibolab.platform import Platform
from qibolab.serialize import (
    load_instrument_settings,
    load_qubits,
    load_runcard,
    load_settings,
)

NAME = "qblox"
ADDRESS = "192.168.0.20"
TIME_OF_FLIGHT = 500
RUNCARD = pathlib.Path(__file__).parent / "qw5q_gold.yml"

instruments_settings = {
    "cluster": Cluster_Settings(reference_clock_source=ReferenceClockSource.INTERNAL),
    "qrm_rf_a": ClusterQRM_RF_Settings(  # q0,q1,q5, 1-2-4?
        {
            "o1": ClusterRF_OutputPort_Settings(
                channel="L3-25_a",
                attenuation=36,  # 38
                lo_frequency=7_300_000_000,
                gain=0.6,
            ),
            "i1": QbloxInputPort_Settings(
                channel="L2-5_a",
                acquisition_hold_off=TIME_OF_FLIGHT,
                acquisition_duration=900,
            ),
        }
    ),
    "qrm_rf_b": ClusterQRM_RF_Settings(  # q2,q3,q4
        {
            "o1": ClusterRF_OutputPort_Settings(
                channel="L3-25_b",
                attenuation=36,  # 32
                lo_frequency=7_850_000_000,
                gain=0.6,
            ),
            "i1": QbloxInputPort_Settings(
                channel="L2-5_b",
                acquisition_hold_off=TIME_OF_FLIGHT,
                acquisition_duration=900,
            ),
        }
    ),
    "qcm_rf0": ClusterQCM_RF_Settings(
        {
            "o1": ClusterRF_OutputPort_Settings(
                channel="L3-15",
                attenuation=20,
                lo_frequency=5_052_833_073,
                gain=0.470,
            ),
            "o2": ClusterRF_OutputPort_Settings(
                channel="L3-11",
                attenuation=20,
                lo_frequency=5_052_833_073,
                gain=0.570,
            ),
        }
    ),
    "qcm_rf1": ClusterQCM_RF_Settings(
        {
            "o1": ClusterRF_OutputPort_Settings(
                channel="L3-12",
                attenuation=20,
                lo_frequency=5_995_371_914,
                gain=0.550,
            ),
            "o2": ClusterRF_OutputPort_Settings(
                channel="L3-13",
                attenuation=20,
                lo_frequency=6_961_018_001,
                gain=0.596,
            ),
        }
    ),
    "qcm_rf2": ClusterQCM_RF_Settings(
        {
            "o1": ClusterRF_OutputPort_Settings(
                channel="L3-14",
                attenuation=20,
                lo_frequency=6_786_543_060,
                gain=0.470,
            )
        }
    ),
    "qcm_bb0": ClusterQCM_BB_Settings(
        {
            "o1": ClusterBB_OutputPort_Settings(
                channel="L4-5",
                gain=0.5,
                qubit=0,  # channel="L4-1", gain=0.5, offset=0.2244, qubit=1
            ),
            "o2": ClusterBB_OutputPort_Settings(
                channel="L4-1",
                gain=0.5,
                qubit=1,  # channel="L4-2", gain=0.5, offset=-0.3762, qubit=2
            ),
            "o3": ClusterBB_OutputPort_Settings(
                channel="L4-2",
                gain=0.5,
                qubit=2,  # channel="L4-3", gain=0.5, offset=-0.8893, qubit=3
            ),
            "o4": ClusterBB_OutputPort_Settings(
                channel="L4-3",
                gain=0.5,
                qubit=3,  # channel="L4-4", gain=0.5, offset=0.5915, qubit=4
            ),
        }
    ),
    "qcm_bb1": ClusterQCM_BB_Settings(
        {
            "o1": ClusterBB_OutputPort_Settings(
                channel="L4-4",
                gain=0.5,
                qubit=4,  # channel="L4-5", gain=0.5, offset=0.5544, qubit=0
            )
        }
    ),
}


def create(runcard_path=RUNCARD):
    """QuantWare 5q-chip controlled using qblox cluster.

    Args:
        runcard_path (str): Path to the runcard file.
    """

    def instantiate_module(modules, cls, name, address, settings):
        module_settings = settings[name]
        modules[name] = cls(name=name, address=address, settings=module_settings)
        return modules[name]

    modules = {}

    cluster = Cluster(
        name="cluster",
        address="192.168.0.20",
        settings=instruments_settings["cluster"],
    )

    qrm_rf_a = instantiate_module(
        modules, ClusterQRM_RF, "qrm_rf_a", "192.168.0.20:16", instruments_settings
    )  # qubits q0, q1, q5
    qrm_rf_b = instantiate_module(
        modules, ClusterQRM_RF, "qrm_rf_b", "192.168.0.20:18", instruments_settings
    )  # qubits q2, q3, q4

    qcm_rf0 = instantiate_module(
        modules, ClusterQCM_RF, "qcm_rf0", "192.168.0.20:6", instruments_settings
    )  # qubit q0
    qcm_rf1 = instantiate_module(
        modules, ClusterQCM_RF, "qcm_rf1", "192.168.0.20:8", instruments_settings
    )  # qubits q1, q2
    qcm_rf2 = instantiate_module(
        modules, ClusterQCM_RF, "qcm_rf2", "192.168.0.20:10", instruments_settings
    )  # qubits q3, q4

    qcm_bb0 = instantiate_module(
        modules, ClusterQCM_BB, "qcm_bb0", "192.168.0.20:2", instruments_settings
    )  # qubit q0
    qcm_bb1 = instantiate_module(
        modules, ClusterQCM_BB, "qcm_bb1", "192.168.0.20:4", instruments_settings
    )  # qubits q1, q2, q3, q4

    # DEBUG: debug folder = report folder
    # import os
    # folder = os.path.dirname(runcard) + "/debug/"
    # if not os.path.exists(folder):
    #     os.makedirs(folder)
    # for name in modules:
    #     modules[name]._debug_folder = folder

    controller = QbloxController("qblox_controller", cluster, modules)
    twpa_pump = SGS100A(name="twpa_pump", address="192.168.0.36")

    # Create channel objects
    channels = {}
    # readout
    channels["L3-25_a"] = Channel(name="L3-25_a", port=qrm_rf_a.ports["o1"])
    channels["L3-25_b"] = Channel(name="L3-25_b", port=qrm_rf_b.ports["o1"])

    # feedback
    channels["L2-5_a"] = Channel(name="L2-5_a", port=qrm_rf_a.ports["i1"])
    channels["L2-5_b"] = Channel(name="L2-5_b", port=qrm_rf_b.ports["i1"])

    # drive
    channels["L3-15"] = Channel(name="L3-15", port=qcm_rf0.ports["o1"])
    channels["L3-11"] = Channel(name="L3-11", port=qcm_rf0.ports["o2"])
    channels["L3-12"] = Channel(name="L3-12", port=qcm_rf1.ports["o1"])
    channels["L3-13"] = Channel(name="L3-13", port=qcm_rf1.ports["o2"])
    channels["L3-14"] = Channel(name="L3-14", port=qcm_rf2.ports["o1"])

    # flux
    channels["L4-5"] = Channel(name="L4-5", port=qcm_bb0.ports["o1"])
    channels["L4-1"] = Channel(name="L4-1", port=qcm_bb0.ports["o2"])
    channels["L4-2"] = Channel(name="L4-2", port=qcm_bb0.ports["o3"])
    channels["L4-3"] = Channel(name="L4-3", port=qcm_bb0.ports["o4"])
    channels["L4-4"] = Channel(name="L4-4", port=qcm_bb1.ports["o1"])

    # TWPA
    channels["L3-28"] = Channel(name="L3-28", port=None)
    channels["L3-28"].local_oscillator = twpa_pump

    # create qubit objects
    runcard = load_runcard(runcard_path)
    qubits, couplers, pairs = load_qubits(runcard)
    # remove witness qubit
    # del qubits[5]
    # assign channels to qubits
    for q in [0, 1]:
        qubits[q].readout = channels["L3-25_a"]
        qubits[q].feedback = channels["L2-5_a"]
        qubits[q].twpa = channels["L3-28"]
    for q in [2, 3, 4]:
        qubits[q].readout = channels["L3-25_b"]
        qubits[q].feedback = channels["L2-5_b"]
        qubits[q].twpa = channels["L3-28"]

    qubits[0].drive = channels["L3-15"]
    qubits[0].flux = channels["L4-5"]
    channels["L4-5"].qubit = qubits[0]
    for q in range(1, 5):
        qubits[q].drive = channels[f"L3-{10 + q}"]
        qubits[q].flux = channels[f"L4-{q}"]
        channels[f"L4-{q}"].qubit = qubits[q]

    # set maximum allowed bias
    for q in range(5):
        qubits[q].flux.max_bias = 2.5

    instruments = {controller.name: controller, twpa_pump.name: twpa_pump}
    settings = load_settings(runcard)
    instruments = load_instrument_settings(runcard, instruments)
    return Platform(
        "qw5q_gold_qblox", qubits, pairs, instruments, settings, resonator_type="2D"
    )
