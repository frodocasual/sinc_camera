import json

import time
from typing import List
from queue import Empty
import multiprocessing as mp
from multiprocessing import Queue, Manager
from multiprocessing.managers import ValueProxy

import cv2
import neoapi

from camera import Camera
from camera_baumer import CameraBaumer


def initialize_cameras(
    cam_to_found_number: int = 1, 
    cameras_serial_numbers: list[str] = []
    ) -> list[Camera]:

    cameras = CameraBaumer.get_available_cameras(cam_to_found_number, cameras_serial_numbers)
    for i, camera in enumerate(cameras):
        if i == 0: 
            camera.line_selector = neoapi.LineSelector_Line1 
            camera.line_mode = neoapi.LineMode_Output 
            camera.line_source = neoapi.LineSource_ExposureActive 
         
        # Set next camera as slave for trigger wait 
        if i != 0: 
            camera.trigger_mode = neoapi.TriggerMode_On

    return cameras


def store_images(q: Queue, files_stored: ValueProxy[int]):
    while True:
        try:
            file_name, img = q.get(timeout=2)
        except Empty:
            return
        
        cv2.imwrite(file_name, img)
        
        files_stored.value = files_stored.value + 1


def get_images(
        cameras: List[Camera],
    ) -> list[list[int|str]]:
    
    image_pairs_captured = 0
    
    files_to_store_queue = Queue()

    manager = Manager()
    files_stored = manager.Value('i', 0)

    processes = [
        mp.Process(target=store_images, args=[files_to_store_queue, files_stored]),
        mp.Process(target=store_images, args=[files_to_store_queue, files_stored]),
        mp.Process(target=store_images, args=[files_to_store_queue, files_stored]),
        mp.Process(target=store_images, args=[files_to_store_queue, files_stored]),
    ]

    [proc.start() for proc in processes]
    
    for cam_num, camera in enumerate(cameras):
        cv2.namedWindow(f'camera_{cam_num}', cv2.WINDOW_NORMAL) 
        cv2.resizeWindow(f'camera_{cam_num}', 800, 600)

    image_pairs_captured_start = image_pairs_captured
    files_stored_start = files_stored.value
    start = time.perf_counter()
    recorded_info = []

    while True:

        sync_recorded_info = []

        for cam_num, camera in enumerate(cameras):
            img, timestamp = camera.get_image()
            
            cv2.imshow(f'camera_{cam_num}', img)

            file_name = RESULTS_PATH +"/" f'camera_{cam_num}_{image_pairs_captured}{".png"}'

            files_to_store_queue.put((file_name, img))
            
            sync_recorded_info.extend((timestamp, file_name))

        recorded_info.append(sync_recorded_info)
        
        image_pairs_captured = image_pairs_captured + 1

        k = cv2.waitKey(1)

        if time.perf_counter() - start > 1:
            fps_read = (image_pairs_captured - image_pairs_captured_start) / (time.perf_counter() - start)
            fps_write = (files_stored.value - files_stored_start) / (time.perf_counter() - start)
            print(f'Images captured {image_pairs_captured}, FPS {fps_read:.1f}, write speed {fps_write:.1f}, queue size {files_to_store_queue.qsize()}')

            image_pairs_captured_start = image_pairs_captured
            files_stored_start = files_stored.value
            start = time.perf_counter() 
        
        if k == 27:  # Escape
            print(f'Stopping capturing, waiting for {files_to_store_queue.qsize()} files to write in parallel processes..')
            files_to_store_queue.close()
            break

    for process in processes:
        process.join()

    print(f'Captured stopped: {image_pairs_captured*2} images captured, {files_stored.value} files written')

    return recorded_info


if __name__ == "__main__":
    RESULTS_PATH = r"results"
    
    cameras = initialize_cameras(cam_to_found_number=2)
    print("Camera has been connected...")
    
    for camera in cameras:
        camera.gain = 2
        camera.exposure = 10_000
        camera.frame_rate_enable = True
        camera.frame_rate = 30.0

    recorded_info = get_images(cameras)

    with open('recorded_data.json', 'w') as fp:
        json.dump(recorded_info, fp, indent=4)
        print('Recorded data is saved to recorded_data.json') 