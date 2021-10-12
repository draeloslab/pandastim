import numpy as np

import cv2
import zmq

from pathlib import Path


class CalibrationException(Exception):
    """
    Blob detection for calibration failed
    """
    pass


def reduce_to_pi(ar):
    """Reduce angles to the -pi to pi range"""
    return np.mod(ar + np.pi, np.pi * 2) - np.pi


def angle_mean(angles, axis=0):
    """Correct calculation of a mean of an array of angles
    """
    return np.arctan2(np.sum(np.sin(angles), axis), np.sum(np.cos(angles), axis))


class StimulusCalibrator:
    def __init__(self, camera_img, proj_pts):

        self.camera_img = camera_img
        self.projected_pts = np.array(proj_pts)
        self.projected_pts = self.projected_pts[np.argsort(self._find_angles(self.projected_pts)), :]
        self.camera_pts = self._find_triangle(self.camera_img)

    def transforms(self):
        x_proj = np.vstack([self.projected_pts.T, np.ones(3)])
        x_cam = np.vstack([self.camera_pts.T, np.ones(3)])
        proj_to_camera = self.camera_pts.T @ np.linalg.inv(x_proj)
        camera_to_proj = self.projected_pts.T @ np.linalg.inv(x_cam)

        print('cam coords:', self.camera_pts)
        print('projected in cam coords:', cv2.transform(np.reshape(self.projected_pts, (3, 1, 2)), proj_to_camera))
        return proj_to_camera, camera_to_proj

    def return_means(self):
        return np.mean(self.camera_pts, axis=0)

    @staticmethod
    def _find_triangle(image, blob_params=None):
        blob_params = cv2.SimpleBlobDetector_Params()
        blob_params.maxThreshold = 255;
        if blob_params is None:
            blobdet = cv2.SimpleBlobDetector_create()
        else:
            blobdet = cv2.SimpleBlobDetector_create(blob_params)

        scaled_im = 255 - (image.astype(np.float32) * 255 / np.max(image)).astype(
            np.uint8
        )
        keypoints = blobdet.detect(scaled_im)
        if len(keypoints) != 3:
            raise CalibrationException("3 points for calibration not found")
        kps = np.array([k.pt for k in keypoints])

        # Find the angles between the points
        # and return the points sorted by the angles

        return kps[np.argsort(StimulusCalibrator._find_angles(kps)), :]

    @staticmethod
    def _find_angles(kps):
        angles = np.empty(3)
        for i, pt in enumerate(kps):
            pt_prev = kps[(i - 1) % 3]
            pt_next = kps[(i + 1) % 3]
            # angles are calculated from the dot product
            angles[i] = np.abs(
                np.arccos(
                    np.sum((pt_prev - pt) * (pt_next - pt)) / np.product(
                        [np.sqrt(np.sum((pt2 - pt) ** 2)) for pt2 in [pt_prev, pt_next]]
                    )
                )
            )
        return angles


def img_receiver(socket, flags=0):
    string = socket.recv_string(flags=flags)
    msg_dict = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags)
    _img = np.frombuffer(bytes(memoryview(msg)), dtype=msg_dict['dtype'])
    img = _img.reshape(msg_dict['shape'])
    return np.array(img)


def calibrator(input_socket, point_dump):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'calibration')
    socket.connect(str("tcp://localhost:") + str(input_socket))

    outputs = img_receiver(socket)
    img = outputs
    print('got image')
    # mywind = gw.getWindowsWithTitle('calibrator_triangle')[0]
    # mywind.close()
    proj_pts = point_dump.get()
    proj_to_camera, camera_to_proj = StimulusCalibrator(img, proj_pts).transforms()
    parentPath = Path(__file__).parent.resolve()
    np.save(parentPath.joinpath('_cam2proj.npy'), camera_to_proj)
    np.save(parentPath.joinpath('_proj2cam.npy'), proj_to_camera)
