import numpy as np
from collections import namedtuple

Block = namedtuple("Block", ["x", "y", "size", "data"])

def dcPred264(block, top, left):
    if left.data.size == 0 or top.data.size == 0:
        return

    dc = (np.mean(left.data[0 : left.size, -1]) +
          np.mean(top.data[-1, 0: top.size])) / 2.0
    block.data[:, :] = dc

# top row and left column are handled differently in the h.265 case
def dcPred265(block, top, left):
    if left.data.size == 0 or top.data.size == 0:
        return

    dc = (np.mean(left.data[0 : left.size, -1]) +
          np.mean(top.data[-1, 0: top.size])) / 2.0

    block.data[0, 0] = (2 * dc + top.data[-1, 0] + left.data[0, -1]) / 4.0
    block.data[1:, 0] = (3 * dc + left.data[1:, -1]) / 4.0
    block.data[0, 1:] = (3 * dc + top.data[-1, 1:]) / 4.0
    block.data[1:, 1:] = dc


def planePred264(block, top, left):
    pass

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
        block.data[:, :] = top.data[-1, 0: top.size]

def horizontalPred(block, top, left):
    if left.data.size > 0:
        block.data[:, :] = np.matrix(left.data[0 : left.size, -1]).T

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
def predAVC(image, area, predictionType):
    # reject invalid areas
    if (area.x < 0 or area.y < 0 or
        area.y + area.size > image.shape[0] or
        area.x + area.size > image.shape[1]):
        print "ignoring area", area.x, area.y, area.size
        return image

    # subdivide area into 4x4 prediction blocks
    # or 16x16 macroblocks?
    # (plane-mode is normally only applicable for 16x16)
    blocks = getBlocks(image, area, 16)

    # predict blocks with selected predictionType
    predict = {"dc": dcPred264, "plane": planePred264,
               "vertical": verticalPred, "horizontal": horizontalPred}
    predictBlocks(blocks, predict[predictionType])

    return image

# fill in invalidated areas with HEVC prediction
def predHEVC(image, area, predictionType):
    # same as AVC but with other blocksizes??

    # reject invalid areas
    if (area.x < 0 or area.y < 0 or
        area.y + area.size > image.shape[0] or
        area.x + area.size > image.shape[1]):
        print "ignoring area", area.x, area.y, area.size
        return image

    # subdivide area into 16x16 prediction blocks
    blocks = getBlocks(image, area, 16)

    # predict blocks with selected predictionType
    predict = {"dc": dcPred265, "plane": planarPred265,
               "vertical": verticalPred, "horizontal": horizontalPred}
    predictBlocks(blocks, predict[predictionType])
    return image
