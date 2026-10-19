#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import os
import csv
import time
from datetime import datetime, timezone

app = Flask(__name__)

# Lokasi file CSV
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "rest_log.csv")

# Kolom log sesuai LKM 2
FIELDNAMES = [
    "timestamp_iso",
    "node_id",
    "protocol",
    "t_send_ms",
    "t_recv_ms",
    "payload_bytes",
    "suhu",
    "sequence_no"
]


# Membuat CSV dan header jika file belum ada atau kosong
def initialize_csv():
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


initialize_csv()


# Endpoint pencatatan suhu
@app.route("/add", methods=["GET"])
def add_numbers():
    # Waktu server menerima request
    t_recv_ms = int(time.time() * 1000)

    # Mengambil parameter request
    node_id = request.args.get("node_id", "unknown")
    t_send_ms = request.args.get("t_send_ms")
    sequence_no = request.args.get("sequence_no")
    suhu = request.args.get("suhu")

    # Menghitung ukuran query string dalam byte
    payload_bytes = len(request.query_string)

    try:
        t_send_ms = int(t_send_ms)
        sequence_no = int(sequence_no)
        suhu = float(suhu)

    except (TypeError, ValueError):
        return jsonify({"error": "Invalid telemetry parameters"}), 400

    # Waktu ISO 8601 UTC
    timestamp_iso = datetime.now(timezone.utc).isoformat()

    # Data log
    row = {
        "timestamp_iso": timestamp_iso,
        "node_id": node_id,
        "protocol": "rest",
        "t_send_ms": t_send_ms,
        "t_recv_ms": t_recv_ms,
        "payload_bytes": payload_bytes,
        "suhu": suhu,
        "sequence_no": sequence_no
    }

    # Simpan ke CSV
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)

    print(
        f"REST received: node={node_id}, "
        f"seq={sequence_no}, suhu={suhu}°C, "
        f"bytes={payload_bytes}"
    )

    # Respons ke client
    return jsonify({
        "result": "success",
        "node_id": node_id,
        "sequence_no": sequence_no,
        "suhu": suhu,
        "t_recv_ms": t_recv_ms
    })


# Endpoint perkalian tetap tersedia
@app.route("/mul", methods=["GET"])
def mul_numbers():
    try:
        a = int(request.args.get("a"))
        b = int(request.args.get("b"))
        return jsonify({"result": a * b})

    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input"}), 400


# Jalankan server
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5151,
        debug=False
    )