import math
import numpy as np
from collections import namedtuple

Block = namedtuple("Block", ["x", "y", "size", "data"])

def dcPred264(block, top, left):
    if left.data.size == 0 or top.data.size == 0:
        return

    dc = (np.mean(left.data[:, -1]) +
          np.mean(top.data[-1, :])) / 2.0
    block.data[:, :] = dc

# top row and left column are handled differently in the h.265 case
def dcPred265(block, top, left):
    if left.data.size == 0 or top.data.size == 0:
        return

    dc = (np.mean(left.data[:, -1]) +
          np.mean(top.data[-1, :])) / 2.0

    block.data[0, 0] = (2 * dc + top.data[-1, 0] + left.data[0, -1]) / 4.0
    block.data[1:, 0] = (3 * dc + left.data[1:, -1]) / 4.0
    block.data[0, 1:] = (3 * dc + top.data[-1, 1:]) / 4.0
    block.data[1:, 1:] = dc


def planePred264(block, top, left):
    if block.size != 16:
	    print "h264 plane mode only works for 16x16 blocks"
	    return

    if top.data.size > 0 and left.data.size > 0:
	    leftPixels = left.data[:, -1].astype("int")
	    topPixels = top.data[-1, :].astype("int")
	    H = 0
	    for i in range(1, 9):
	        A = i*(topPixels[7+i]-topPixels[8-i])
	        H = H + A
	    V = 0
	    for i in range(1, 9):
	        A = i*(topPixels[7+i]-topPixels[8-i])
	        V = V + A


	    H = (5*H + 32) / 64
	    V = (5*V + 32) / 64

	    a = 16 * (leftPixels[15] + topPixels[15] + 1) - 7*(V+H)
	    for i in range(16):
	        for j in range(16):
		    b = a + V * j + H * i
		    block.data[i,j] = min(max(b/32, 0), 255)

# Shorter version, doesn't work atm
def planePred264_2(block, top, left):
    if left.data.size == 0 or top.data.size == 0:
        return

    leftPixels = left.data[:, -1].astype("int")
    topPixels = top.data[-1, :].astype("int")

    bs = block.size
    bsh = block.size / 2
    print "foo", bs, bsh

    H = np.sum(np.arange(1, bsh + 1) * (topPixels[bsh:] - top.data[:bsh][::-1]))
    V = np.sum(np.arange(1, bsh + 1) * (leftPixels[bsh:] - left.data[:bsh][::-1]))

    H = (5 * H + 32) / 64
    V = (5 * V + 32) / 64
    a = 16 * (leftPixels[-1] + topPixels[-1] + 1) - (bsh - 1) * (V + H)
    for y in range(block.size):
        for x in range(block.size):
            b = a + V * y + H * x
            block.data[y, x] = max(min(b / 32, 255), 0)

def planarPred265(block, top, left, topRight=None, bottomLeft=None):
    if left.data.size == 0 or top.data.size == 0:
        return

    bs = block.size

    # determine a,d references
    if bottomLeft is not None:
        refA = bottomLeft.data[0, -1]
    else:
        refA = left.data[-1, -1]

    if topRight is not None:
        refD = topRight.data[-1, 0]
    else:
        refD = top.data[-1, -1]

    for y in range(bs):
        for x in range(bs):
            refB = left.data[y, -1]
            refC = top.data[-1, x]
            block.data[y, x] = (y + 1) / (2.0*bs) * refA + \
                               (bs - 1 - x) / (2.0*bs) * refB + \
                               (bs - 1 - y) / (2.0*bs) * refC + \
                               (x + 1) / (2.0*bs) * refD

def verticalPred(block, top, left):
    if top.data.size > 0:
        block.data[:, :] = top.data[-1, :]

def horizontalPred(block, top, left):
    if left.data.size > 0:
        block.data[:, :] = np.matrix(left.data[:, -1]).T

# divide area into prediction blocks
def getBlocks(image, area, blockSize):
    # align top-left x/y edge
    alignedX = area.x - area.x % blockSize
    alignedY = area.y - area.y % blockSize

    # add one row/column on the top/left for reference blocks
    prevX, prevY = alignedX - blockSize, alignedY - blockSize

    # get prediction blockcounts
    countX = np.ceil((area.x - prevX + area.size * 2) / blockSize)
    countY = np.ceil((area.y - prevY + area.size * 2) / blockSize)

    # create prediction blocks
    blocks = []
    for bY in range(int(countY)):
        blocks.append([])
        for bX in range(int(countX)):
            xPos = prevX + bX * blockSize
            yPos = prevY + bY * blockSize
            blocks[bY].append(Block(
                x = xPos,
                y = yPos,
                size = blockSize,
                data = image[yPos : yPos + blockSize, xPos : xPos + blockSize]
            ))
    return blocks

# predict blocks in order from top-left to bottom-right
def predictBlocks(blocks, predictionFunc):
    # don't predict the first row/column, they are references
    for bY in range(1, len(blocks) - 1):
        for bX in range(1, len(blocks[bY]) - 1):
            # prediction block
            block = blocks[bY][bX]

            # get reference blocks
            tBlock = blocks[bY - 1][bX]
            lBlock = blocks[bY][bX - 1]

            predictionFunc(block, tBlock, lBlock)

# fill in invalidated areas with AVC prediction
def predAVC(image, area, predictionType, blockSize):
    # reject invalid areas
    if (area.x < 0 or area.y < 0 or
        area.y + area.size > image.shape[0] or
        area.x + area.size > image.shape[1]):
        print "ignoring area", area.x, area.y, area.size
        return image

    # subdivide area into 4x4 prediction blocks
    # or 16x16 macroblocks?
    # (plane-mode is only applicable for 16x16)
    blocks = getBlocks(image, area, blockSize)

    # predict blocks with selected predictionType
    predict = {"dc": dcPred264, "plane": planePred264,
               "vertical": verticalPred, "horizontal": horizontalPred}
    predictBlocks(blocks, predict[predictionType])

    return image

# fill in invalidated areas with HEVC prediction
def predHEVC(image, area, predictionType, blockSize):
    # same as AVC but with other blocksizes??

    # reject invalid areas
    if (area.x < 0 or area.y < 0 or
        area.y + area.size > image.shape[0] or
        area.x + area.size > image.shape[1]):
        print "ignoring area", area.x, area.y, area.size
        return image

    # subdivide area into 4x4 - 64x64 prediction blocks
    blocks = getBlocks(image, area, blockSize)

    # predict blocks with selected predictionType
    predict = {"dc": dcPred265, "plane": planarPred265,
               "vertical": verticalPred, "horizontal": horizontalPred}
    predictBlocks(blocks, predict[predictionType])
    return image
