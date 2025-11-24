# RaceIntel360

A comprehensive F1 racing data analytics platform built with FastAPI and FastF1. Collect, store, and analyze Formula 1 race data with ease.

## Features

- **Data Collection**: Automated F1 data fetching using FastF1 library
- **RESTful API**: FastAPI-based backend with comprehensive endpoints
- **PostgreSQL Database**: Robust data storage with optimized schema
- **Analytics**: Built-in analytics and comparison tools
- **Real-time Updates**: Support for incremental data updates

## Project Structure

```
raceintel360/
├── data_pipeline/        # Data collection scripts
│   ├── fetch_f1_data.py  # Script to fetch and populate the database
│   └── requirements.txt  # Python dependencies (FastF1, pandas, etc.)
├── api/                  # FastAPI application
│   ├── main.py           # FastAPI app definition
│   ├── models.py         # Pydantic models and/or DB ORM models
│   ├── database.py       # Database connection management
│   ├── routes/           # API route definitions (split by domain)
│   │   ├── races.py      # Race-related endpoints
│   │   ├── drivers.py    # Driver-related endpoints
│   │   ├── laps.py       # Lap data endpoints
│   │   └── analytics.py  # Analytics endpoints
│   └── requirements.txt  # Dependencies (FastAPI, uvicorn, asyncpg, etc.)
├── config/               # Configuration files
│   ├── config.example.env # Example environment variables
│   └── db_setup.sql      # SQL script to create tables
├── scripts/              # Utility scripts
│   ├── install.sh        # Bash script to install packages
│   └── run_server.sh     # Script to start the FastAPI server
└── README.md             # This file
```

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip package manager
- Bash shell (for running scripts)

## Installation

### Quick Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd raceintel360
```

2. Run the installation script:
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

3. Set up the database:
```bash
# Create database
createdb raceintel360

# Or using psql:
# psql -U postgres
# CREATE DATABASE raceintel360;
# \q

# Run setup script
psql raceintel360 -f config/db_setup.sql
```

4. Configure environment variables:
```bash
cp config/config.example.env config/config.env
# Edit config/config.env with your database credentials
```

5. Activate virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Manual Installation

If you prefer to install manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r data_pipeline/requirements.txt
pip install -r api/requirements.txt

# Set up database (same as above)
```

## Usage

### Running the Data Pipeline

Fetch and populate F1 data:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the data pipeline
python data_pipeline/fetch_f1_data.py
```

You can modify `fetch_f1_data.py` to:
- Fetch specific years/seasons
- Include telemetry data
- Update incremental data

Example usage in Python:
```python
from data_pipeline.fetch_f1_data import F1DataPipeline
import asyncio

async def main():
    pipeline = F1DataPipeline()
    await pipeline.connect()
    
    # Fetch recent seasons
    await pipeline.fetch_recent_seasons([2024], include_telemetry=False)
    
    # Or fetch specific sessions
    await pipeline.fetch_and_store_session_data(2024, 'Monaco', 'R')
    
    await pipeline.close()

asyncio.run(main())
```

### Starting the API Server

**Option 1: Using the script**
```bash
chmod +x scripts/run_server.sh
./scripts/run_server.sh
```

**Option 2: Using uvicorn directly**
```bash
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using Python**
```bash
source venv/bin/activate
python -m api.main
```

The API will be available at:
- **Base URL**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - API information
- `GET /health` - Health check with database status

### Races
- `GET /api/v1/races` - List races with filters (year, country)
- `GET /api/v1/races/{race_id}` - Get race by ID
- `GET /api/v1/races/{race_id}/summary` - Get race summary with driver stats

### Drivers
- `GET /api/v1/drivers` - List all drivers
- `GET /api/v1/drivers/{driver_name}/stats` - Get driver statistics

### Laps
- `GET /api/v1/laps` - List laps with filters
- `GET /api/v1/laps/{lap_id}` - Get lap by ID
- `GET /api/v1/laps/race/{race_id}/fastest` - Get fastest laps per driver

### Analytics
- `GET /api/v1/analytics/driver-comparison` - Compare two drivers
- `GET /api/v1/analytics/circuit-performance` - Get circuit statistics
- `GET /api/v1/analytics/season-summary` - Get season summary

## Example API Calls

```bash
# Get all races from 2024
curl http://localhost:8000/api/v1/races?year=2024

# Get race summary
curl http://localhost:8000/api/v1/races/1/summary

# Compare two drivers
curl "http://localhost:8000/api/v1/analytics/driver-comparison?driver_1=VER&driver_2=HAM"

# Get season summary
curl http://localhost:8000/api/v1/analytics/season-summary?year=2024

# Get circuit performance
curl "http://localhost:8000/api/v1/analytics/circuit-performance?location=Monaco"
```

## Configuration

Edit `config/config.env` to configure:

- **Database**: Connection string and credentials
- **API**: Host, port, and CORS origins
- **FastF1**: Cache directory and settings
- **Environment**: Debug mode and log level

## Database Schema

### Tables

- **races**: Race event information
  - race_id, year, round, country, location, date, race_name, circuit_name, etc.

- **laps**: Lap-by-lap data
  - lap_id, race_id, driver_number, driver, lap_number, lap_time, sectors, compounds, etc.

### Views

- **race_summary**: Aggregated race statistics
- **driver_race_stats**: Driver performance per race

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style

```bash
# Install linting tools
pip install black flake8 mypy

# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Adding New Endpoints

1. Create route file in `api/routes/` if needed
2. Add Pydantic models to `api/models.py`
3. Register router in `api/main.py`
4. Update this README with new endpoints

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `config/config.env`
- Ensure database exists: `psql -l | grep raceintel360`

### Data Fetching Issues

- Check internet connection
- Verify FastF1 cache directory permissions
- Check for API rate limits

### Import Errors

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python3 --version`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [FastF1](https://github.com/theOehrly/Fast-F1) for F1 data access
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- Formula 1 data providers

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review code comments

---

**RaceIntel360** - Drive your F1 data analysis forward! 🏎️📊

