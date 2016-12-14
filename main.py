#!/usr/bin/env python3
# Implement the HEVC and AVC planar intra prediction
# for block sizes of 16x16 and 32x32 and compare
# reconstruction results subjectively and objectively
import numpy as np
import cv2
from pred import *
from videolib import yuvVideo

# definition of variables
width = 1920;
height = 1088;
numInvalids = 16;
predictionType = "planar" # select from "planar", "dc", "vertical", "horizontal"

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
    blockSize   = invalidBlocks[j, 2]
    endX        = startX + blockSize
    endY        = startY + blockSize

    predImage[startY:endY, startX:endX] = 0;

# show image with holes to be filled by prediction
cv2.imshow('original with empty blocks', predImage)

# TODO: implement two functions predicting the invalidated parts
# with 'AVC/HEVC Planar'. The functions should have the following headers:
# function predImage = planarPredAVC(inputImage,posX,posY,blockSize)
# and
# function predImage = planarPredHEVC(inputImage,posX,posY,blockSize)
predImageHEVC   = predImage
predImageAVC    = predImage

for j in range(numInvalids * 2):
    area = invalidBlocks[j]
    #x      = invalidBlocks[j, 0]
    #y      = invalidBlocks[j, 1]
    #size   = invalidBlocks[j, 2]

    # first, fill holes by AVC planar prediction
    predImageAVC = predAVC(predImageAVC, area, predictionType)

    # next, fill holes by HEVC planar prediction
    predImageHEVC = predHEVC(predImageHEVC, area, predictionType)

# TODO: compute difference image between original and predicted images
# diffAVC =
# diffHEVC =

# TODO: compute PSNR between original and predicted images
# PSNR_AVC =
# PSNR_HEVC =

# show final predicted images
cv2.imshow('AVC image', predImageAVC)
cv2.imshow('HEVC image', predImageHEVC)

while True:
    key = cv2.waitKey(200) & 0xff;
    if key == ord('q'):
        break

# Release everything if job is finished
cv2.destroyAllWindows()
