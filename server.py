import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import stripe

# Inizializzazione app
app = FastAPI()

# Configurazione CORS per permettere la connessione dal frontend su Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurazione Database MongoDB Atlas
MONGO_URL = os.environ.get("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database("missionefitness") # Nome del database

# Configurazione Stripe
stripe.api_key = os.environ.get("STRIPE_API_KEY")

class CheckoutRequest(BaseModel):
    package_id: str
    success_url: str
    cancel_url: str

@app.get("/")
def read_root():
    return {"status": "Backend di Missione Fitness attivo e online!"}

@app.get("/api/packages")
get_packages = async def get_packages():
    # Recupera i pacchetti salvati nel database
    packages = []
    async for pkg in db.packages.find():
        pkg["_id"] = str(pkg["_id"])
        packages.append(pkg)
    return packages

@app.post("/api/create-checkout-session")
async def create_checkout_session(data: CheckoutRequest):
    try:
        # Creazione della sessione di pagamento con Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Pacchetto Fitness: {data.package_id}',
                    },
                    'unit_amount': 5000, # Prezzo di esempio in centesimi (50.00€)
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
