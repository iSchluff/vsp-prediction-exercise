#!/usr/bin/env python2
# Implement the HEVC and AVC planar intra prediction
# for block sizes of 16x16 and 32x32 and compare
# reconstruction results subjectively and objectively
import numpy as np
import cv2
from pred import *
from videolib import yuvVideo

# definition of variables
width = 1920
height = 1088
numInvalids = 16
blockSize = 16
predictionType = "plane" # select from "plane", "dc", "vertical", "horizontal"

# read yuv file (only luminance is loaded)
video = yuvVideo('Dancer_1920x1088.yuv', width, height)
origImage = np.array(video.readFrame(0), dtype='u1')

cv2.imshow('original', origImage)

# define regions to be invalidated (vector contains y, x and size)
invalidBlocks = np.zeros((numInvalids * 2, 3))
for j in range(numInvalids):
   invalidBlocks[j] = np.array([(height / numInvalids)*j, (width / numInvalids)*j, 16], dtype='u4')
   invalidBlocks[j + numInvalids] = np.array([height - (height / numInvalids) * j, (width / numInvalids) * j, 32], dtype='u4')

# invalidate parts of the image, which need to be predicted
predImage = origImage.copy();
for j in range(numInvalids*2):
    # invalidate block
    startY      = invalidBlocks[j, 0]
    startX      = invalidBlocks[j, 1]
    size        = invalidBlocks[j, 2]
    endX        = startX + size
    endY        = startY + size

    predImage[startY:endY, startX:endX] = 0;

# show image with holes to be filled by prediction
cv2.imshow('original with empty blocks', predImage)

predImageHEVC   = predImage.copy()
predImageAVC    = predImage.copy()

for j in range(numInvalids * 2):
    area = Block(
        y = invalidBlocks[j, 0],
        x = invalidBlocks[j, 1],
        size = invalidBlocks[j, 2],
        data = None
    )

    # fill holes by AVC/HEVC prediction
    predImageAVC = predAVC(predImageAVC, area, predictionType, blockSize)
    predImageHEVC = predHEVC(predImageHEVC, area, predictionType, blockSize)

# compute difference image between original and predicted images
cv2.imshow('AVC Diff', np.subtract(origImage, predImageAVC))
cv2.imshow('HEVC Diff', np.subtract(origImage, predImageHEVC))

# the 'Mean Squared Error' between the two images is the
# sum of the squared difference between the two images;
def mse(imageA, imageB):
	err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])
	return err

# compute PSNR
PSNR_AVC = 10 * np.log10(255**2 / mse(origImage, predImageAVC))
PSNR_HEVC = 10 * np.log10(255**2 / mse(origImage, predImageHEVC))
print 'PSNR AVC:', PSNR_AVC
print 'PSNR HEVC:', PSNR_HEVC

# show final predicted images
cv2.imshow('AVC image', predImageAVC)
cv2.imshow('HEVC image', predImageHEVC)

while True:
    key = cv2.waitKey(200) & 0xff;
    if key == ord('q'):
        break

# Release everything if job is finished
cv2.destroyAllWindows()
