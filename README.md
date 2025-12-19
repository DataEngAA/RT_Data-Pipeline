# Cricket Data Platform (CDP)

A real-time cricket match simulation platform that generates ball-by-ball events, streams them through Kafka, and provides multiple consumers for visualization and analysis.

## Architecture

- **Match Simulator** (`run_match.py`): Generates realistic ball-by-ball cricket match events
- **Kafka**: Message broker for real-time event streaming
- **Consumers**:
  - Console Consumer (`run_consumer_console.py`): Live match commentary
  - SQLite Consumer (`run_consumer_sqlite.py`): Persists events to SQLite database

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Kafka)
- (Optional) WSL or Git Bash on Windows (for running shell scripts)

## Quick Start

1. **Set up Python environment:**
   ```powershell
   # Create and activate virtual environment
   python -m venv .venv
   .\.venv\Scripts\activate

   # Install package in editable mode
   python -m pip install -e .
   ```

2. **Start Kafka:**
   ```powershell
   # Start Kafka and Zookeeper
   docker-compose up -d

   # Verify Kafka is running
   docker-compose ps
   ```

3. **Create Kafka topics:**
   ```powershell
   # Using Git Bash or WSL
   bash ./scripts/create_topics.sh

   # Or manually:
   docker exec cdp-kafka kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 3 --topic cricket_live --config retention.ms=604800000 --config cleanup.policy=delete
   ```

4. **Run the simulation:**
   ```powershell
   # Start console consumer (in one terminal)
   python run_consumer_console.py

   # Start SQLite consumer (in another terminal)
   python run_consumer_sqlite.py

   # Start match simulator (in another terminal)
   python run_match.py
   ```

## Verifying the Setup

### 1. Check Kafka

Kafka broker should be accessible at `localhost:9092`. To verify:

```powershell
# Check if containers are running
docker-compose ps

# View Kafka logs
docker-compose logs -f kafka

# List topics
docker exec cdp-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Describe topics
docker exec cdp-kafka kafka-topics --bootstrap-server localhost:9092 --describe
```

### 2. Check Data Flow

The simulator sends events to topic `cricket_live`. To verify:

```powershell
# Watch live events
docker exec cdp-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic cricket_live --from-beginning

# Check SQLite database
python scripts/analyze_cricket_db.py  # Shows recent events and exports to CSV
```

### 3. Monitor Resources

- SQLite database: `data/cricket.db`
- CSV export: `data/cricket_balls.csv`
- Kafka data: Persisted in Docker volumes (see `docker-compose.yml`)

## Stopping the Stack

```powershell
# Stop simulator and consumers: Ctrl+C in their terminals

# Stop Kafka stack
docker-compose down
```

## Development

- Source code under `src/cricket/`
- Configuration in `config/`
- Database and exports in `data/`
- Helper scripts in `scripts/`

## Troubleshooting

1. **Kafka Connection Issues**
   - Ensure Docker is running
   - Check `docker-compose ps` shows both services up
   - Verify `localhost:9092` is accessible
   - Check Kafka logs: `docker-compose logs kafka`

2. **Import Errors**
   - Ensure package is installed: `pip install -e .`
   - Check virtual environment is activated
   - In VS Code: Select correct interpreter (from `.venv`)

3. **Data Issues**
   - Check SQLite database exists: `data/cricket.db`
   - View recent events: `python scripts/analyze_cricket_db.py`
   - Monitor Kafka consumer lag (if events seem delayed)


Integrate real-time analytics (e.g., Flink / Pinot)
