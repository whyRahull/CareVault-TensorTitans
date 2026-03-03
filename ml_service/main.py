"""
CareVault ML Service
====================
Unified FastAPI service that exposes all ML capabilities as REST API endpoints.

Routes
------
GET  /health                     Health check
POST /api/violence/detect        Violence / suspicious activity detection (YOLO + XGBoost)
POST /api/hand_sos/detect        Hand SOS gesture detection (MediaPipe + TFLite)
POST /api/severity/predict       Incident severity prediction (TF-IDF + sklearn)
POST /api/sos/send               Emergency SOS email alert
POST /api/sos/travel             Travel-details emergency alert
POST /api/lost_child/search      Lost child face search (placeholder)

Docs: http://localhost:8001/docs
"""

from fastapi import FastAPI

from routers import violence, hand_sos, severity, sos, lost_child

app = FastAPI(
    title="CareVault ML Service",
    description=(
        "AI/ML microservice for CareVault — violence detection, hand SOS, "
        "severity prediction, SOS alerts and lost child search."
    ),
    version="1.0.0",
)

# --------------------------------------------------------------------------
# Routers
# --------------------------------------------------------------------------
app.include_router(violence.router,   prefix="/api/violence",   tags=["Violence Detection"])
app.include_router(hand_sos.router,   prefix="/api/hand_sos",   tags=["Hand SOS"])
app.include_router(severity.router,   prefix="/api/severity",   tags=["Severity Prediction"])
app.include_router(sos.router,        prefix="/api/sos",        tags=["SOS Alert"])
app.include_router(lost_child.router, prefix="/api/lost_child", tags=["Lost Child Search"])


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------
@app.get("/health", tags=["Health"], summary="Service health check")
async def health_check():
    return {"status": "ok", "service": "CareVault ML Service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
