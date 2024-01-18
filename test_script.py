from typing import Any, Dict
from fastapi import FastAPI
from uvicorn import run

app = FastAPI()


@app.get("/get_cores")
def get_cores():  
    return {"res": "wow"}


@app.post("/hello")
def halt_task(item: Dict):
    print(item["hello"])
    return {}


def run_server():
    run(app, host="127.0.0.1", port=8201, log_level="critical")
    return 

if __name__ == "__main__":
    run_server()