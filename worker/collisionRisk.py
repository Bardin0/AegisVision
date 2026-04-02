
def getCenterPoint(bbox):
    x1, y1, x2, y2 = bbox
    xCenter = (x1 + x2) / 2
    yCenter = (y1 + y2) / 2
    return (xCenter, yCenter)

def distance(coord1, coord2):
    c1 = getCenterPoint(coord1)
    c2 = getCenterPoint(coord2)

    #Euclidian dist formula
    return (float(c1[0] - c2[0]) ** 2 + float(c1[1] - c2[1]) ** 2) ** 0.5

def isPersonDriving(person_bbox, vehicle_bbox, vehicle_label):
    if vehicle_label in ["bicycle", "motorbike"]:
        # simple overlap check
        x1, y1, x2, y2 = person_bbox
        vx1, vy1, vx2, vy2 = vehicle_bbox
        return not (x2 < vx1 or x1 > vx2 or y2 < vy1 or y1 > vy2)
    return False

def overlapRatio(bbox1, bbox2):
    # calculate intersection area
    x1, y1, x2, y2 = bbox1
    x1_v, y1_v, x2_v, y2_v = bbox2

    xi1 = max(x1, x1_v)
    yi1 = max(y1, y1_v)
    xi2 = min(x2, x2_v)
    yi2 = min(y2, y2_v)

    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    inter_area = inter_width * inter_height

    # area of the smaller box (usually the person)
    person_area = (x2 - x1) * (y2 - y1)
    if person_area == 0:
        return 0
    return inter_area / person_area  # fraction of person overlapping vehicle