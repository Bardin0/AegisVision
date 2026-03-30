import boto3
import shutil
import os
import json
from ultralytics import YOLO
from datetime import datetime
from decimal import Decimal

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
        results = model(local_path, save=True)

        detections = []

        for r in results:

            for box in r.boxes:

                detections.append({
                    "label": model.names[int(box.cls)],
                    "confidence": Decimal(str(float(box.conf))),
                    "bbox": [Decimal(str(float(coord))) for coord in box.xyxy.view(-1).tolist()]
                })

        # Store results
        table.put_item(
            Item={
                "image_key": key,
                "timestamp": datetime.utcnow().isoformat(),
                "objects": detections
            }
        )
        saved_path = os.path.join(results[0].save_dir, os.path.basename(local_path))
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
