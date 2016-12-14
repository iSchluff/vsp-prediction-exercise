import os
import numpy as np

class yuvVideo:
    def __init__(self, path, width, height, fps=25):
        self.fd = open(path, 'rb')
        self.width = width
        self.height = height
        self.fps = fps
        self.planeSize = self.width * self.height
        self.frameSize = int(self.planeSize * 8 / 8) # 8 bits per pixel
        self.fileSize = os.stat(path).st_size
        self.numFrames = self.fileSize / self.frameSize

    # read y-component from i420 frame
    def readFrame(self, frame):
        self.fd.seek(frame * self.frameSize)
        y = self.fd.read(self.planeSize)
        # v = self.fd.read(self.planeSize / 4)
        # u = self.fd.read(self.planeSize / 4)
        return np.fromstring(y, np.uint8).reshape((self.height, self.width))

    def close(self):
        self.fd.close()

    def __str__(self):
        return "(Video size: %d, frames: %d)" % (self.fileSize, self.numFrames)
