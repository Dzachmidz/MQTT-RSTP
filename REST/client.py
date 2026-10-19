#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import csv
import os
import uuid

# URL REST server di MacBook
# url = "http://172.20.10.2:5151/add"
url = "https://factsheet-properly-freeway.ngrok-free.dev/add"


# Identitas client
node_id = "rest-client-04"
sequence_no = 0
suhu = 28
session_id = str(uuid.uuid4())

# File CSV di folder yang sama dengan client.py
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(base_dir, "rest_client_log.csv")

fieldnames = [
    "timestamp_iso",
    "node_id",
    "protocol",
    "t_send_ms",
    "t_response_ms",
    "rtt_ms",
    "sequence_no",
    "status_code"
]

# Buat CSV dan header jika file belum ada atau kosong
if not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0:
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

print(f"REST Client: {node_id}")
print("Mengirim request setiap 1 detik. Tekan Ctrl+C untuk berhenti.")

try:
    while True:
        sequence_no += 1

        # Timestamp epoch milliseconds untuk log
        t_send_ms = int(time.time() * 1000)

        # Timer monotonic untuk mengukur RTT
        start = time.perf_counter()

        try:
            response = requests.get(
                url,
                params={
                    "node_id": node_id,
                    "t_send_ms": t_send_ms,
                    "sequence_no": sequence_no,
                    "suhu": suhu,
                    "session_id": session_id
                },
                timeout=5
            )

            end = time.perf_counter()

            # RTT tidak bergantung pada sinkronisasi jam kedua laptop
            rtt_ms = round((end - start) * 1000, 3)
            t_response_ms = int(time.time() * 1000)

            timestamp_iso = time.strftime(
                "%Y-%m-%dT%H:%M:%S",
                time.gmtime()
            ) + f".{int((t_response_ms % 1000)) :03d}+00:00"

            row = {
                "timestamp_iso": timestamp_iso,
                "node_id": node_id,
                "protocol": "rest",
                "t_send_ms": t_send_ms,
                "t_response_ms": t_response_ms,
                "rtt_ms": rtt_ms,
                "sequence_no": sequence_no,
                "status_code": response.status_code
            }

            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)

            if response.status_code == 200:
                print(
                    f"seq={sequence_no}, "
                    f"status={response.status_code}, "
                    f"RTT={rtt_ms} ms"
                )
            else:
                print(
                    f"seq={sequence_no}, "
                    f"status={response.status_code}, "
                    f"RTT={rtt_ms} ms"
                )

        except requests.RequestException as e:
            print(f"Request seq={sequence_no} gagal: {e}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nREST Client dihentikan.")
    print(f"Log RTT tersimpan di: {csv_file}")