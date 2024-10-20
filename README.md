# Tripo Python Client

This is a Python client for the Tripo API.

## Installation

```bash
pip install tripo
```

```bash
export TRIPO_API_KEY="your_api_key"
```

## Usage

```python
from tripo import Client

with Client() as client:
    balance = client.get_balance()
    print(f"Balance: {balance.balance}, Frozen: {balance.frozen}")
```

```python
from tripo import Client, FileToken

# Initialize the client
with Client() as client:
    # Create a task to generate a model from text
    success_task = client.text_to_model(
        prompt="A 3D model of a futuristic car",
        texture=True,
        pbr=True
    )
    print(f"Created task with ID: {success_task.task_id}")

    # Get 3d model
    data = client.try_download_model(success_task.task_id)
    with open("model.glb", "wb") as f:
        f.write(data.model)
```

```python
from tripo import Client, FileToken

# Initialize the client
with Client() as client:
    # Upload a file
    upload_data = client.upload_file('path/to/your/image.jpg')
    print(f"Uploaded file token: {upload_data.image_token}")

    # Create a task to generate a model from an image
    success_task = client.image_to_model(
        file_token=upload_data.image_token,
        model_version='v1.4-20240625',
        texture=True,
        pbr=True
    )
    print(f"Created task with ID: {success_task.task_id}")

    # Get 3d model
    data = client.try_download_model(success_task.task_id)
    with open("model.glb", "wb") as f:
        f.write(data.model)
```
