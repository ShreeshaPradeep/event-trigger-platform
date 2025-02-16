from mangum import Mangum
from app.main import app

# Create ASGI handler
handler = Mangum(app) 