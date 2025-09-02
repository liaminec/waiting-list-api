from fastapi import FastAPI
from participations.routes import router as participations_router
from users.routes import router as users_router

app = FastAPI()

app.include_router(participations_router)
app.include_router(users_router)
