from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
from pathlib import Path
from statistics import mean

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Access-Control-Allow-Origin"],
)

data_path = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"

with open(data_path, encoding="utf-8") as f:
    telemetry = json.load(f)


class RequestData(BaseModel):
    regions: List[str]
    threshold_ms: float


def percentile(values, p):
    values = sorted(values)

    if not values:
        return 0

    position = (len(values) - 1) * p / 100
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    return values[lower] + (values[upper] - values[lower]) * (position - lower)


@app.post("/")
def analytics(request: RequestData):
    result = {}

    for region in request.regions:
        records = [
            record for record in telemetry
            if record["region"] == region
        ]

        latencies = [record["latency_ms"] for record in records]
        uptimes = [record["uptime_pct"] for record in records]

        result[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": mean(uptimes),
            "breaches": sum(
                record["latency_ms"] > request.threshold_ms
                for record in records
            )
        }

    return result

