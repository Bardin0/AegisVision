import boto3
import shutil
import os
import json
from ultralytics import YOLO
from datetime import datetime
from decimal import Decimal
import cv2
from collisionRisk import getCenterPoint, distance

sqs = boto3.client("sqs")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/934463280694/aegis-queue.fifo"
TABLE_NAME = "aegis-inference-results"

table = dynamodb.Table(TABLE_NAME)

model = YOLO("yolov8s.pt")
print("Everything set up well")

while True:

    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])

    for message in messages:

        print("Processing Message: ", message)
        job = json.loads(message["Body"])

        bucket = job["bucket"]
        key = job["image_key"]

        local_path = f"/tmp/{message['MessageId']}.jpg"

        # Download image
        s3.download_file(bucket, key, local_path)

        # Run YOLO inference
        results = model(local_path, save=False)

        detections = []

        for r in results:

            for box in r.boxes:

                detections.append({
                    "label": model.names[int(box.cls)],
                    "confidence": Decimal(str(float(box.conf))),
                    "bbox": [Decimal(str(float(coord))) for coord in box.xyxy.view(-1).tolist()]
                })

        saved_path = os.path.join(results[0].save_dir, os.path.basename(local_path))

        # getting potential collision risks
        risks = []
        people = [d for d in detections if d["label"] == "person"]
        vehicles = [d for d in detections if d["label"] in ["car", "truck", "bus", "motorbike", "train", "bicycle"]]

        for vehicle in vehicles:
            for person in people:
                dist = distance(person["bbox"], vehicle["bbox"])

                if dist < 150:
                    risks.append({
                        "type": "risk",
                        "labels": [vehicle["label"], person["label"]],
                        "bboxes": [vehicle["bbox"], person["bbox"]],
                        "distance": Decimal(str(float((dist))))
                    })

        risk_boxes = set()
        for risk in risks:
            for box in risk["bboxes"]:
                # convert Decimal to tuple of ints for comparison
                risk_boxes.add(tuple(map(int, box)))

        img = cv2.imread(local_path)

        # Draw all non-risk detections in blue
        for d in detections:
            box = tuple(map(int, d["bbox"]))
            if box in risk_boxes:
                continue  # skip risk boxes
            x1, y1, x2, y2 = box
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)  # blue for normal

        for risk in risks:
            box1, box2 = [tuple(map(int, b)) for b in risk["bboxes"]]

            for box in [box1, box2]:
                x1, y1, x2, y2 = box
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)  # red for risk

            # Draw "RISK" text
            cx = int((box1[0] + box2[0]) / 2)
            cy = int((box1[1] + box2[1]) / 2)
            cv2.putText(img, "RISK", (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Save the annotated image
        cv2.imwrite(saved_path, img)

        for risk in risks:
            print("---------- Detected risk:")
            print("  Objects:", risk["labels"])
            print("  Distance:", risk["distance"])
            print("  BBoxes:", risk["bboxes"])

        # Store results
        table.put_item(
            Item={
                "image_key": key,
                "timestamp": datetime.utcnow().isoformat(),
                "objects": detections,
                "risks": risks
            }
        )
        filename = os.path.basename(key) 
        newKey = f"annotated/{filename}"

        s3.upload_file(
                saved_path,
                bucket,
                newKey,
                ExtraArgs={'ContentType': 'image/jpeg'}
            )

        # Remove job from queue
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=message["ReceiptHandle"]
        )

        if os.path.exists(results[0].save_dir):
            shutil.rmtree(results[0].save_dir)
            print(f"Cleaned up: {results[0].save_dir}")


        print("Processed:", key)
