from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    assignment, auth, charity, contact, cra_request, cycle,
    evaluation, financial_acquisition, note, priority, sector,
)

app = FastAPI(title="Evaluator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(assignment.router)
app.include_router(auth.router)
app.include_router(charity.router)
app.include_router(sector.router)
app.include_router(contact.router)
app.include_router(cra_request.router)
app.include_router(cycle.router)
app.include_router(evaluation.router)
app.include_router(financial_acquisition.router)
app.include_router(note.router)
app.include_router(priority.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "evaluator"}
