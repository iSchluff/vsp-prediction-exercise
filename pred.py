def dcPred():
    pass

def planarPred():
    pass

def verticalPred():
    pass

def horizontalPred():
    pass

# divide area into prediction blocks
def getBlocks(x, y, size, blockSize):
    return []

# fill in invalidated areas with AVC prediction
def predAVC(image, area, predictionType):

    # subdivide area into prediction blocks
    blocks = getBlocks(area[0], area[1], area[2], 4)

    # predict blocks with selected predictionType
    for block in blocks:
        if predictionType == "dc":
            pass
        elif predictionType == "planar":
            pass
        elif predictionType == "horizontal":
            pass
        elif predictiontype == "vertical":
            pass

    return image

# fill in invalidated areas with HEVC prediction
def predHEVC(image, area, predictionType):
    # same as AVC but with other blocksizes?
    return image
