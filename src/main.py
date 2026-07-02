from fastapi import FastAPI
from routes import router as index_html

app = FastAPI()

app.include_router(index_html)
