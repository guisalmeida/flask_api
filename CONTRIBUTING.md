# Contributing

### How to run the dockerfile locally
```
docker run -dp 5000:5000 -w /app -v $(pwd):/app flask_api:latest sh -c "flask run --host 0.0.0.0"
```

### Run RQ worker locally (linux/macos)
```
rq worker -u <redis URL> emails
```