
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import laps as laps_routes
from api.routes import races as races_routes
from api.routes import strategy as strategy_routes

logging.basicConfig(  #configure logging
    level=logging.INFO,  #set log level to info
    format="%(asctime)s - api.main - %(levelname)s - %(message)s",  #log format
)
log = logging.getLogger("api.main")

app = FastAPI(   #create FastAPI app
    title="RaceIntel360 API",  #api title
    version="0.1.0",
    description=(
        "Backend for RaceIntel360: races, laps, telemetry (optional), "
        "stats (optional)."
    ),
    openapi_tags=[   #api tags for documentation
        {"name": "Health", "description": "Service status"},
        {"name": "Races", "description": "Race list and details from the DB"},
        {"name": "Laps", "description": "Lap data per race/driver from the DB"},
        {"name": "Telemetry", "description": "On-demand FastF1 telemetry"},
        {"name": "Stats", "description": "DB row counts (optional)"},
        {"name": "Strategy", "description": "Race strategy simulation"},
        {"name": "AI Analysis", "description": "AI-powered strategy analysis"},
        {"name": "Analytics", "description": "Advanced analytics and comparisons"},
        {"name": "Drivers", "description": "Driver information and statistics"},
    ],
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "RaceIntel360 API"
    }

# CORS for local + HF Spaces
app.add_middleware(  
    CORSMiddleware,
    allow_origins=[  #list of allowed origins
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://*.hf.space",
        "https://*.hf.live",
    ],
    allow_credentials=True, #allow credentials  
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---
@app.get("/", tags=["Health"])      #root endpoint
def root():
    """Root endpoint with API information."""
    return {"status": "ok", "service": "RaceIntel360 API"}

 
@app.get("/healthz", tags=["Health"])  #health check endpoint
def healthz():
    """Health check endpoint."""
    return {"ok": True}



app.include_router(races_routes.router, tags=["Races"]) #get race data
app.include_router(laps_routes.router, tags=["Laps"]) #get lap data
app.include_router(strategy_routes.router, tags=["Strategy"]) #get strategy simulation


for mod_name, tag in (  #optional routers
    ("telemetry", "Telemetry"), #get telemetry data
    ("stats", "Stats"),
    ("ai_analysis", "AI Analysis"), #ai-powered analysis
    ("analytics", "Analytics"),
    ("drivers", "Drivers"), #get driver information
):
    try:
        mod = __import__(f"api.routes.{mod_name}", fromlist=["router"]) #import module
        app.include_router(mod.router, tags=[tag]) #include router
        log.info(f"Loaded optional router: {mod_name}") #log success
    except Exception as e:
        log.info(f"Optional router '{mod_name}' not loaded: {e}")


if __name__ == "__main__":
    import uvicorn #run the app with uvicorn

    log.info("Starting RaceIntel360 API...") #log startup
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True) #run the app
