import time
from tripo import Client

# Initialize the client
with Client() as client:
    # Create a task to generate a model from text
    success_task = client.text_to_model(
        prompt="A 3D model of a futuristic car",
        model_version="v2.0-20240919",
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
