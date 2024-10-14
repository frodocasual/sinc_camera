from __future__ import annotations

from typing import List
import time
import numpy as np

try:
    import neoapi
except ImportError:
    neoapi_found = False
else:
    neoapi_found = True

from camera import Camera


class CameraBaumer(Camera):
    def __init__(self, camera: neoapi.Cam, serial_number: str = None):
        self.camera = camera
        if serial_number is not None:
            self.camera.Connect(serial_number)            
        else:
            self.camera.Connect()
        self.type = 'baumer'
        
        # Sync system and camera time
        self.camera.f.TimestampReset.Execute()        
        self.system_timestamp_shift = time.time_ns()


    @staticmethod
    def get_available_cameras(cameras_num_to_find: int = 1, cameras_serial_numbers: List[str] = []) -> list[Camera]:
        cameras = []

        if neoapi_found:
            i = 0
            
            while i < cameras_num_to_find:
                # Get next camera from neoapi
                if len(cameras_serial_numbers) == 0:
                    camera = CameraBaumer(neoapi.Cam())
                else:
                    camera = CameraBaumer(neoapi.Cam(), cameras_serial_numbers[i])
                    if camera.camera.f.DeviceSerialNumber.value not in cameras_serial_numbers:
                        raise Exception(f'Error, camera serial number is not {cameras_serial_numbers[i]}')
                
                # Set default cameras parameters
                camera.exposure = 20_000
                camera.gain = 2.0
                camera.frame_rate_enable = True
                camera.frame_rate = 10.0
                camera.camera.f.PixelFormat = neoapi.PixelFormat_Mono8

                cameras.append(camera)
                i = i + 1
        return cameras

    def get_image(self) -> np.array:
        baumer_image = self.camera.GetImage()
        img = baumer_image.GetNPArray()
        timestamp = baumer_image.GetTimestamp() + self.system_timestamp_shift
        return img.reshape(img.shape[0], img.shape[1]), timestamp
    

    @property
    def exposure(self):
        return self.camera.f.ExposureTime.value

    @exposure.setter
    def exposure(self, x):
        self.camera.f.ExposureTime.value = x

    @property
    def gain(self):
        return self.camera.f.Gain.value

    @gain.setter
    def gain(self, x):
        self.camera.f.Gain.value = x

    @property
    def gamma(self):
        return self.camera.f.Gamma.value

    @gamma.setter
    def gamma(self, x):
        self.camera.f.Gamma.value = x

    @property
    def exposure_auto(self):
        return self.camera.f.ExposureAuto.value

    @exposure_auto.setter
    def exposure_auto(self, x):
        self.camera.f.ExposureAuto.value = x

    @property
    def trigger_mode(self):
        return self.camera.f.TriggerMode.value

    @trigger_mode.setter
    def trigger_mode(self, x):
        self.camera.f.TriggerMode.value = x

    @property
    def line_selector(self):
        return self.camera.f.LineSelector.value

    @line_selector.setter
    def line_selector(self, x):
        self.camera.f.LineSelector.value = x

    @property
    def line_mode(self):
        return self.camera.f.LineMode.value

    @line_mode.setter
    def line_mode(self, x):
        self.camera.f.LineMode.value = x

    @property
    def line_source(self):
        return self.camera.f.LineSource.value

    @line_source.setter
    def line_source(self, x):
        self.camera.f.LineSource.value = x

    @property
    def frame_rate_enable(self):
        return self.camera.f.AcquisitionFrameRateEnable.value

    @frame_rate_enable.setter
    def frame_rate_enable(self, x):
        self.camera.f.AcquisitionFrameRateEnable.value = x

    @property
    def frame_rate(self):
        return self.camera.f.AcquisitionFrameRate.value

    @frame_rate.setter
    def frame_rate(self, x):
        self.camera.f.AcquisitionFrameRate.value = x