# DongLoRa MeshCore Analyser — Codex Plan File

## Objective
Build a **MeshCore-focused LoRa analyser** on top of the DongLoRa stack for the **Australian narrow MeshCore preset around 916 MHz**.

This tool is **not** a general RF spectrum analyser and must not attempt to be one. DongLoRa is a USB-controlled LoRa radio interface, not an IQ-sampling SDR. The analyser should therefore focus on:

- fixed-profile packet monitoring
- packet logging with metadata
- airtime estimation
- repeated-packet/fingerprint grouping
- simple live web dashboard
- optional narrow fallback sweep around the known MeshCore profile

## Context
DongLoRa exposes a firmware protocol over USB and has a Python client library already available. The firmware supports configuring radio parameters and streaming received LoRa packets with RSSI and SNR metadata.

Relevant capabilities already present in the upstream stack:
- host-configurable frequency, bandwidth, SF, CR, sync word, preamble, TX power, and CAD
- `StartRx` / `StopRx`
- unsolicited `RxPacket` frames while receiving
- Python client package with `connect()`, `send()`, and `recv()`

## Hard Requirements
1. Use **Python** for the MVP.
2. Use the existing **donglora** Python client package where practical.
3. Treat the target radio profile as a **known preset**, not a discovery problem.
4. Store packet history in **SQLite**.
5. Provide a **local web UI** and **JSON API**.
6. Keep the architecture simple enough to run on a Raspberry Pi.
7. Do **not** implement speculative protocol decoding unless there is a clean plugin boundary.
8. Prefer a working fixed-profile monitor before any sweep logic.

## Non-Goals
- no SDR/IQ sample capture
- no waterfall/spectrum display
- no wideband scanning
- no attempt to decode arbitrary protocols by guesswork
- no transmit features in the initial MVP except where needed for connectivity tests

## Assumed Initial Profile
Create a named profile for the expected MeshCore AU narrow settings:

```yaml
name: au_narrow_916
freq_hz: 916000000
bw: 62.5
sf: 7
cr: 8
sync_word: 0x12
preamble_len: 16
cad: true
```

Notes:
- This profile should be editable in config.
- Internally, bandwidth must be translated to the DongLoRa bandwidth enum.
- Frequency may need fine adjustment later if the actual MeshCore preset uses an offset from exactly 916.000 MHz.

## Expected DongLoRa Protocol Facts
Build around these assumptions from upstream:
- USB CDC-ACM transport
- COBS framing with `0x00` sentinel
- `SetConfig`, `StartRx`, `StopRx`
- `RxPacket` contains `rssi`, `snr`, `len`, `payload`
- bandwidth enum includes **62.5 kHz**
- the Python client can already connect and receive packets

## Deliverables
Codex should produce the following:

1. A runnable Python project.
2. A CLI with at least these commands:
   - `init-db`
   - `monitor`
   - `serve`
   - `sweep` (optional but scaffolded)
3. SQLite schema and migrations/init logic.
4. A collector that continuously receives packets from DongLoRa.
5. Basic LoRa airtime estimation.
6. A small local dashboard.
7. A short README with setup and run instructions.
8. Unit tests for core pure functions.

## Suggested Tech Stack
- Python 3.11+
- `donglora`
- `FastAPI` or `Flask` for the API/UI
- `sqlite3` or `SQLAlchemy` with SQLite backend
- standard-library threading/asyncio only if needed
- minimal frontend: server-rendered HTML or very light JS

Use the simplest option that keeps the code maintainable.

## Project Layout
```text
meshcore-analyser/
├─ pyproject.toml
├─ README.md
├─ .env.example
├─ analyser/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ cli.py
│  ├─ radio.py
│  ├─ collector.py
│  ├─ storage.py
│  ├─ models.py
│  ├─ airtime.py
│  ├─ fingerprint.py
│  ├─ stats.py
│  ├─ api.py
│  ├─ profiles.py
│  └─ templates/
│     └─ index.html
├─ scripts/
│  └─ dev_run.sh
└─ tests/
   ├─ test_airtime.py
   ├─ test_fingerprint.py
   └─ test_profiles.py
```

## Functional Requirements

### 1. Profile handling
Implement named radio profiles.

Requirements:
- load default profile from code or config file
- support future multiple profiles
- convert human values into DongLoRa-compatible config
- validate bounds before sending to device

### 2. Radio adapter
Implement a thin wrapper around the `donglora` Python client.

Responsibilities:
- connect to device
- apply config
- start RX
- stop RX
- normalize packet objects into internal format
- expose clean exceptions and reconnect handling

Do not reimplement the wire protocol unless absolutely necessary.

### 3. Collector
Implement a long-running monitor loop.

For each packet:
- timestamp it in UTC
- record RSSI
- record SNR
- record payload length
- store full payload as hex
- compute SHA-256 of payload
- compute short prefix fields for grouping
- estimate airtime using current profile
- write record to SQLite
- make latest packets available to the web layer

### 4. Storage
Implement SQLite schema initialization and query helpers.

Tables required:

#### `radio_profiles`
- id
- name
- freq_hz
- bw_khz
- sf
- cr
- sync_word
- preamble_len
- cad
- created_at

#### `packets`
- id
- ts_utc
- profile_id
- rssi_dbm
- snr_db
- payload_len
- payload_hex
- payload_sha256
- prefix_hex_4
- prefix_hex_8
- airtime_ms_est
- duplicate_key

Optional later:
- `packet_groups`
- `app_events`

### 5. Fingerprinting
Implement lightweight grouping logic.

At minimum:
- full payload SHA-256
- first 4 bytes as hex prefix if available
- first 8 bytes as hex prefix if available
- duplicate key based on payload hash + short rolling time bucket

Purpose:
- identify repeated packets
- cluster likely adverts/beacons
- show dominant traffic families without pretending to fully decode MeshCore

### 6. Airtime estimation
Implement a pure function:
- input: bandwidth, SF, CR, preamble length, payload length, CRC/header assumptions
- output: estimated airtime in milliseconds

Keep the calculation isolated and documented.

### 7. API
Provide JSON endpoints:
- `GET /health`
- `GET /api/profile`
- `GET /api/packets/recent?limit=100`
- `GET /api/stats/summary`
- `GET /api/stats/timeseries?minutes=60`
- `GET /api/fingerprints/top?limit=50`

### 8. Web UI
Provide one simple dashboard page showing:
- collector status
- current radio profile
- recent packet table
- packets per minute
- estimated airtime per minute
- average RSSI
- average SNR
- top repeated fingerprints

Keep the UI plain and functional.

## CLI Requirements
Implement commands similar to:

```bash
python -m analyser.cli init-db
python -m analyser.cli monitor --profile au_narrow_916
python -m analyser.cli serve --host 0.0.0.0 --port 8080
python -m analyser.cli sweep --profiles au_narrow_916,au_narrow_916_alt1
```

Behavior:
- `init-db` creates schema
- `monitor` starts collection loop
- `serve` starts web server
- `sweep` is optional in MVP but should at least be scaffolded

## Sweep Mode Constraints
Sweep mode is **secondary**.

If implemented, it must:
- only test a **small** list of candidate profiles
- dwell briefly on each profile
- count packets and summarize hit rate
- avoid claiming comprehensive discovery

Do not implement a wide or continuous blind sweep.

## Suggested Phases

### Phase 1 — Scaffolding
- create project structure
- add config handling
- add profile definition
- add CLI skeleton
- add DB init

### Phase 2 — DongLoRa receive path
- wrap `donglora.connect()`
- send config
- start RX
- receive packets
- print normalized packet lines to console

### Phase 3 — Persistence
- store packets in SQLite
- add recent packet queries
- add stats queries

### Phase 4 — Analysis
- add payload hashes and prefix grouping
- add airtime estimation
- add repeated-packet summaries

### Phase 5 — UI/API
- add JSON API
- add dashboard page
- display live-ish recent packets and summaries

### Phase 6 — Hardening
- reconnect handling
- input validation
- better logging
- tests for pure functions

### Phase 7 — Optional sweep
- add tiny candidate sweep workflow
- summary output only

## Acceptance Criteria
The MVP is done when all of the following are true:

1. The app can connect to a DongLoRa device and configure the radio.
2. The app can remain in RX mode and continuously ingest packets.
3. Each packet is stored with timestamp, RSSI, SNR, payload length, payload hex, payload hash, and airtime estimate.
4. The dashboard shows recent packets and simple aggregate stats.
5. The project runs locally with straightforward setup steps.
6. The code is cleanly structured enough for later MeshCore-specific decoder plugins.

## Implementation Notes
- Prefer correctness and simplicity over premature abstraction.
- Keep functions small and typed.
- Separate pure logic from I/O-heavy code.
- Keep the radio adapter thin.
- Avoid assumptions about MeshCore packet internals unless explicitly encoded behind a plugin interface.
- Make the profile easy to edit without touching core code.

## Testing Requirements
Add tests for:
- profile-to-radio-config conversion
- fingerprint generation
- airtime calculation
- duplicate key generation

If radio integration tests are impractical, keep them manual and document the manual run steps in the README.

## README Requirements
The README should include:
- what this tool is
- what it is not
- hardware assumptions
- Python setup steps
- how to initialize the DB
- how to start monitoring
- how to open the dashboard
- known limitations

## Manual Test Procedure
Document a simple manual flow:
1. attach supported DongLoRa device
2. initialize DB
3. run monitor with `au_narrow_916`
4. run web server
5. confirm packets appear in console and UI
6. confirm packets persist in SQLite

## Stretch Goals
Only after MVP works:
- export CSV/JSON
- configurable retention/pruning
- multiple simultaneous dongles
- packet family drill-down page
- plugin interface for MeshCore-aware decoders
- narrow profile sweep helper

## Final Instruction to Codex
Implement the MVP end-to-end as a working local project, prioritizing the fixed-profile monitor path. Do not overengineer. Do not add speculative decoding logic. Keep the code readable, typed where practical, and easy to extend later.
