import time
from tripo import Client, MultiviewFileTokens

# Initialize the client
with Client() as client:
    # Upload a file
    front_file_token = client.upload_file("front.jpg")
    left_file_token = client.upload_file("left.jpg")
    back_file_token = client.upload_file("back.jpg")
    print(f"Uploaded front file token: {front_file_token.file_token}")
    print(f"Uploaded left file token: {left_file_token.file_token}")
    print(f"Uploaded back file token: {back_file_token.file_token}")
    file_tokens = MultiviewFileTokens(
        front=front_file_token,
        left=left_file_token,
        back=back_file_token,
    )

    # Create a task to generate a model from an image
    success_task = client.multiview_to_model(
        file_tokens=file_tokens,
        model_version="v2.5-20250123",
        texture=True,
        pbr=True,
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
