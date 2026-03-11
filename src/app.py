from flask import Flask, render_template, request, redirect
import boto3
import uuid

app = Flask(__name__)

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

BUCKET_NAME = "aegis-image-bucket"
TABLE_NAME = "aegis-inference-results"

table = dynamodb.Table(TABLE_NAME)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["image"]

    if file.filename == "":
        return "No file selected"

    image_id = str(uuid.uuid4())
    key = f"uploads/{image_id}.jpg"

    s3.upload_fileobj(file, BUCKET_NAME, key)

    return redirect(f"/results/{image_id}")


@app.route("/results/<image_id>")
def results(image_id):
    key = f"uploads/{image_id}.jpg"
    annotated_key = f"annotated/{image_id}.jpg" 

    response = table.get_item(Key={"image_key": key})
    item = response.get("Item")

    image_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': annotated_key},
        ExpiresIn=3600
    )

    return render_template("results.html", item=item, image_url=image_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
