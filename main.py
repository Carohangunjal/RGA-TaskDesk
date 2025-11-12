from fastapi import FastAPI
import datetime

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "RGA TaskDesk is working!", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/app")
async def app_route():
    return {"message": "App is running", "version": "2.1"}

@app.get("/tasks")
async def get_tasks():
    return {"tasks": ["Sample task 1", "Sample task 2"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
