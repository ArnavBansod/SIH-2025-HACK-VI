import uvicorn
from fastapi import FastAPI
from .routers import auth_router, upload_router, students_router
from .database import engine
from . import models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Student Risk Assessment API", version="0.1.0")

# CORS (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(auth_router.router)
app.include_router(upload_router.router)
app.include_router(students_router.router)

@app.on_event("startup")
async def startup():
    # make sure tables exist (simple approach)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Student Risk Assessment service. See /docs for API."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
