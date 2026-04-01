
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

def is_overlapping(bbox1, bbox2):
    x1, y1, x2, y2 = bbox1       # coordinates of first box
    x1_v, y1_v, x2_v, y2_v = bbox2  # coordinates of second box

    # Check if boxes do NOT overlap:
    # If one box is completely to the left, right, above, or below the other
    if x2 < x1_v or x1 > x2_v or y2 < y1_v or y1 > y2_v:
        return False  # no overlap

    return True  # boxes overlap