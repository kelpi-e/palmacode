import contextlib
import enum
from threading import Thread
from dataclasses import dataclass
from typing import List

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from em_st_artifacts.emotional_math import EmotionalMath
from em_st_artifacts.utils.lib_settings import ArtifactDetectSetting, \
    MentalAndSpectralSetting, MathLibSetting
from em_st_artifacts.utils.support_classes import RawChannels, MindData
from neurosdk.brainbit_sensor import BrainBitSensor
from neurosdk.scanner import Scanner
from neurosdk.sensor import Sensor
from neurosdk.cmn_types import *
from em_st_artifacts import emotional_math


@dataclass
class SpectralData:
    alpha: int
    beta: int
    theta: int


class ConnectionState(Enum):
    Connection=0
    Connected=1
    Disconnection=2
    Disconnected=3
    Error=4


@dataclass
class MindDataInst:
    attention: float
    relaxation: float


@dataclass
class MindDataReal:
    attention: float
    relaxation: float


class ResistState(Enum):
    Normal=0
    Bad=1


@dataclass
class ResistValues:
    O1: ResistState
    O2: ResistState
    T3: ResistState
    T4: ResistState


@dataclass
class BrainBitInfo:
    Name: str
    Address: str
    sensor_info: SensorInfo


class BrainBitAdditional:
    def __init__(self, need_reconnect, sensor):
        self.need_reconnect: bool = need_reconnect
        self.bb: BrainBitSensor = sensor
        self.is_signal = False
        self.emotional_math: emotional_math.EmotionalMath=self.__create_emotional_math()

    def __create_emotional_math(self) -> EmotionalMath:
        mls = MathLibSetting(sampling_rate=250,
                             process_win_freq=25,
                             fft_window=1000,
                             n_first_sec_skipped=4,
                             bipolar_mode=True,
                             channels_number=4,
                             channel_for_analysis=0)

        ads = ArtifactDetectSetting(hanning_win_spectrum=True, num_wins_for_quality_avg=125)

        mss = MentalAndSpectralSetting()
        return EmotionalMath(mls, ads, mss)


class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self, work):
        super().__init__()
        self.work = work

    def run(self):
        self.work()
        self.finished.emit()


class BrainBitController(QObject):
    connectionStateChanged = pyqtSignal(str, ConnectionState)
    batteryChanged = pyqtSignal(str, int)
    resistValuesUpdated=pyqtSignal(str, ResistValues)
    mindDataUpdated = pyqtSignal(str, MindDataReal)
    mindDataWithoutCalibrationUpdated = pyqtSignal(str, MindDataInst)
    spectralDataUpdated = pyqtSignal(str, SpectralData)
    isArtefacted = pyqtSignal(str, bool)
    calibrationProcessChanged = pyqtSignal(str, int)
    foundedDevices = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.__calibration_started = False
        self.__scanner = Scanner([SensorFamily.LEBrainBit])
        self.__connected_devices = {}
        self.__disconnected_devices=list()
        self.connected_devices=list()
        self.thread = None
        self.worker = None

    def search_with_result(self, seconds: int, addresses: List[str]):
        def __device_scan():
            self.__scanner.start()
            QThread.sleep(seconds)
            self.__scanner.stop()
            founded = self.__scanner.sensors()
            filtered_sensors = []
            for si in founded:
                if len(addresses) < 1 or si.Address in addresses:
                    filtered_sensors.append(BrainBitInfo(Name=si.Name,
                                                         Address=si.Address,
                                                         sensor_info=si))
            self.foundedDevices.emit(filtered_sensors)

        self.thread = QThread()
        self.worker = Worker(__device_scan)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def connect_to(self, info: BrainBitInfo, need_reconnect: bool = False):
        self.connectionStateChanged.emit(info.Address, ConnectionState.Connection)
        def __device_connection():
            sensor=None
            try:
                sensor = self.__scanner.create_sensor(info.sensor_info)
            except Exception as err:
                print(err)
            try:
                if sensor is not None:
                    sensor.sensorStateChanged = self.__connection_state_changed
                    sensor.batteryChanged = self.__battery_changed
                    self.__connected_devices.update({info.Address: BrainBitAdditional(need_reconnect, sensor)})
                    self.connected_devices.append(info.Address)
                    self.connectionStateChanged.emit(info.Address, ConnectionState.Connected)
                else:
                    self.connectionStateChanged.emit(info.Address, ConnectionState.Error)
            except Exception as err:
                print(err)

        self.thread = QThread()
        self.worker = Worker(__device_connection)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def __event_sensor_founded(self, scanner: Scanner, sensors: List[SensorInfo]):
        scanner.stop()
        for si in sensors:
            if si.Address in self.__disconnected_devices:
                self.__connected_devices[si.Address].bb.connect()
                if self.__connected_devices[si.Address].bb.state != SensorState.StateInRange:
                    scanner.start()
                else:
                    if self.__connected_devices[si.Address].is_signal:
                        self.__execute_command(self.__connected_devices[si.Address].bb, SensorCommand.StartSignal)
                    self.__disconnected_devices.remove(si.Address)
                return
        if len(self.__disconnected_devices) > 0:
            scanner.start()

    def __connection_state_changed(self, sensor: Sensor, state: SensorState):
        self.connectionStateChanged.emit(sensor.address,
                                         ConnectionState.Connected if state == SensorState.StateInRange else ConnectionState.Disconnected)
        if state == SensorState.StateOutOfRange and sensor.address in self.__connected_devices.keys() and \
                self.__connected_devices[sensor.address].need_reconnect:
            self.__disconnected_devices.append(sensor.address)
            self.__scanner.sensorsChanged = self.__event_sensor_founded
            self.__scanner.start()

    def __battery_changed(self, sensor: Sensor, battery: int):
        self.batteryChanged.emit(sensor.address, battery)

    def disconnect_from(self, address: str):
        self.connectionStateChanged.emit(address, ConnectionState.Disconnection)
        if address in self.__disconnected_devices:
            self.__disconnected_devices.remove(address)
            if len(self.__disconnected_devices) < 1:
                self.__scanner.stop()
        sens = self.__connected_devices[address]
        self.__connected_devices.pop(address)
        self.connected_devices.remove(address)
        sens.bb.disconnect()
        sens.bb = None

    def start_resist(self, address: str):
        def on_resist_received(sensor, data):
            try:
                resistValues = ResistValues(O1=ResistState.Normal if data.O1 < 2500000 else ResistState.Bad,
                                            O2=ResistState.Normal if data.O2 < 2500000 else ResistState.Bad,
                                            T3=ResistState.Normal if data.T3 < 2500000 else ResistState.Bad,
                                            T4=ResistState.Normal if data.T4 < 2500000 else ResistState.Bad)
                self.resistValuesUpdated.emit(sensor.address, resistValues)
            except Exception as err:
                print(err)

        try:
            self.__connected_devices[address].bb.resistDataReceived = on_resist_received
            self.__execute_command(self.__connected_devices[address].bb, SensorCommand.StartResist)
        except Exception as err:
            print(err)

    def stop_resist(self, address: str):
        try:
            self.__connected_devices[address].bb.resistDataReceived=None
            self.__execute_command(self.__connected_devices[address].bb, SensorCommand.StopResist)
        except Exception as err:
            print(err)

    def start_calculations(self, address: str):
        def on_signal_received(sensor, data):
            math = self.__connected_devices[address].emotional_math

            raw_channels = []
            for sample in data:
                left_bipolar = sample.T3 - sample.O1
                right_bipolar = sample.T4 - sample.O2
                raw_channels.append(RawChannels(left_bipolar, right_bipolar))

            math.push_bipolars(raw_channels)
            math.process_data_arr()
            mental_data = math.read_mental_data_arr()
            md = MindData(rel_attention=0, rel_relaxation=0, inst_attention=0, inst_relaxation=0)
            has_data = False
            if len(mental_data) > 0:
                has_data = True
                md = mental_data[-1]
            spectral_data = math.read_spectral_data_percents_arr()
            if len(spectral_data) > 0:
                last_sdp = spectral_data[-1]
                a = round(last_sdp.alpha * 100)
                b = round(last_sdp.beta * 100)
                t = 100 - a - b
                sd = SpectralData(alpha=a,
                                  beta=b,
                                  theta=t)
                self.spectralDataUpdated.emit(address, sd)

            self.isArtefacted.emit(address, math.is_both_sides_artifacted())

            if self.__calibration_started:
                if math.calibration_finished():
                    self.__calibration_started=False
                    self.calibrationProcessChanged.emit(address, 100)
                else:
                    self.calibrationProcessChanged.emit(address, math.get_calibration_percents())
            else:
                if has_data:
                    self.mindDataUpdated.emit(address, MindDataReal(attention=md.rel_attention,
                                                                    relaxation=md.rel_relaxation))
            if has_data:
                self.mindDataWithoutCalibrationUpdated.emit(address, MindDataInst(attention=md.inst_attention,
                                                                                 relaxation=md.inst_relaxation))

        try:
            self.__calibration_started = True
            self.__connected_devices[address].emotional_math.start_calibration()
            self.__connected_devices[address].bb.signalDataReceived = on_signal_received
            self.__execute_command(self.__connected_devices[address].bb, SensorCommand.StartSignal)
            self.__connected_devices[address].is_signal = True
        except Exception as err:
            print(err)


    def stop_calculations(self, address: str):
        self.__calibration_started = False
        self.__connected_devices[address].bb.signalDataReceived = None
        self.__execute_command(self.__connected_devices[address].bb, SensorCommand.StopSignal)
        self.__connected_devices[address].is_signal = False

    def __execute_command(self, sensor: Sensor, command: SensorCommand):
        def execute_command():
            try:
                sensor.exec_command(command)
            except Exception as err:
                print(err)
        thread = Thread(target=execute_command)
        thread.start()

    def stop_all(self):
        self.__scanner.stop()
        self.__scanner.sensorsChanged = None
        self.__scanner = None

        for device in self.__connected_devices.values():
            device.bb.disconnect()
            device.bb.sensorStateChanged = None
            device.bb.batteryChanged = None
            device.bb = None
        self.__connected_devices.clear()
        self.connected_devices.clear()
        self.__disconnected_devices.clear()

brain_bit_controller = BrainBitController()