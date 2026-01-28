from fastapi import FastAPI

app = FastAPI(title="Streamline API")

@app.get("/health")
def health():
    return {"status": "ok", "app": "streamline"}
