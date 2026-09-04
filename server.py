import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import stripe

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URL = os.environ.get("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database("missionefitness")

stripe.api_key = os.environ.get("STRIPE_API_KEY")

class CheckoutRequest(BaseModel):
    package_id: str
    success_url: str
    cancel_url: str

@app.get("/")
def read_root():
    return {"status": "Backend di Missione Fitness attivo e online!"}

@app.get("/api/packages")
async def get_packages():
    packages = []
    async for pkg in db.packages.find():
        pkg["_id"] = str(pkg["_id"])
        packages.append(pkg)
    return packages

@app.post("/api/create-checkout-session")
async def create_checkout_session(data: CheckoutRequest):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Pacchetto Fitness: {data.package_id}',
                    },
                    'unit_amount': 5000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=data.success_url,
            cancel_url=data.cancel_url,
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
