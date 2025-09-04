from fastapi import FastAPI
from participations.routes import router as participations_router
from users.routes import router as users_router
from events.routes import router as events_router

app = FastAPI()

app.include_router(participations_router)
app.include_router(users_router)
app.include_router(events_router)
