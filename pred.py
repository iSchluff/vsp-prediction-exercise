import numpy as np
from collections import namedtuple

Block = namedtuple("Block", ["x", "y", "size", "data"])

def dcPred(block, top, left):
    leftPixels = left.data[0 : left.size, -1]
    topPixels = top.data[-1, 0: top.size]
    dc = (np.mean(leftPixels) + np.mean(topPixels)) / 2
    block.data[:, :] = dc

def planePred(block, top, left):
    pass

def verticalPred(block, top, left):
    pass

def horizontalPred(block, top, left):
    pass

predict = {"dc": dcPred, "plane": planePred,
           "vertical": verticalPred, "horizontal": horizontalPred}

# divide area into prediction blocks
def getBlocks(image, area, blockSize):
    # align top-left x/y edge
    alignedX = area.x - area.x % blockSize
    alignedY = area.y - area.y % blockSize

    # add one row/column on the top/left for reference blocks
    prevX, prevY = alignedX - blockSize, alignedY - blockSize

    # get prediction blockcounts
    countX = np.ceil((area.x - prevX + area.size) / blockSize)
    countY = np.ceil((area.y - prevY + area.size) / blockSize)

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
    for bY in range(1, len(blocks)):
        for bX in range(1, len(blocks[bY])):
            # get reference blocks
            tBlock = blocks[bY][bX - 1]
            lBlock = blocks[bY - 1][bX]

            # predict block
            block = blocks[bY][bX]
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
    blocks = getBlocks(image, area, 4)

    # predict blocks with selected predictionType
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
    predictBlocks(blocks, predict[predictionType])
    return image
