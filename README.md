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
