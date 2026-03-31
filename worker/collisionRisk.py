
def getCenterPoint(bbox):
    x1, y1, x2, y2 = bbox
    xCenter = (x1 + x2) / 2
    yCenter = (x1 + x2) / 2
    return (xCenter, yCenter)

def distance(coord1, coord2):
    c1 = getCenterPoint(coord1)
    c2 = getCenterPoint(coord2)

    #Euclidian dist formula
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5