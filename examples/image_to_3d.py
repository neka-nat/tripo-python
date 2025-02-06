import time
from tripo import Client

# Initialize the client
with Client() as client:
    # Upload a file
    file_token = client.upload_file("sample_image.png")
    # Or upload a byte array
    # byte_image = open("sample_image.png", "rb").read()
    # file_token = client.upload_file(byte_image)
    print(f"Uploaded file token: {file_token.file_token}")

    # Create a task to generate a model from an image
    success_task = client.image_to_model(
        file_token=file_token,
        model_version='v2.0-20240919',
        texture=True,
        pbr=True
    )
    print(f"Created task with ID: {success_task.task_id}")

    # Get 3d model
    print("Waiting for the model to be ready...")
    while True:
        data = client.try_download_model(success_task.task_id)
        if data is not None:
            data.save("model.glb")
            break
        time.sleep(1)
