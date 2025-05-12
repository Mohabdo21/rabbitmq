# RabbitMQ Demo

![rabbitmq](https://github.com/user-attachments/assets/44dfcdde-965e-4f0f-befe-dced71987979)


A multi-language demonstration of RabbitMQ producers and consumers implemented in Go, JavaScript, and Python.

## Quick Start

## 1. Start RabbitMQ:

<em>Note: This requires Docker.</em>

```bash
make run
```

## 2. Run implementations:

### Go

```bash
cd go
go run producer/main.go  # :8080
go run consumer/main.go
```

### JavaScript

```bash
cd js
npm install
node producer.js  # :8080
node consumer.js
```

### Python

```bash
cd py
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python producer.py  # :8000
python consumer.py
```

## Access

- Management UI: http://localhost:15672 (guest/guest)
- Producers:
  - Go/JS: `GET /send?msg=hello`
  - Python: `GET /send?msg=hello`
