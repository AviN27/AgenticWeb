from fastapi import FastAPI
from .ride_api import router as ride_router
from .food_api import router as food_router
from .mart_api import router as mart_router
from .payment_api import router as payment_router
from .location_api import router as location_router

app = FastAPI(title="GrabHack Adapter Gateway")

# Mount each domain router
app.include_router(ride_router,     prefix="/ride",    tags=["ride"])
app.include_router(food_router,     prefix="/food",    tags=["food"])
app.include_router(mart_router,     prefix="/mart",    tags=["mart"])
app.include_router(payment_router,  prefix="/payment", tags=["payment"])
app.include_router(location_router, prefix="/location", tags=["location"])