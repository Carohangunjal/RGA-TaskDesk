from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import datetime

app = FastAPI()

# HTML template for the web interface
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>RGA TaskDesk</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .healthy { background: #d4edda; color: #155724; }
        .endpoints { background: #e2e3e5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 RGA TaskDesk</h1>
        <div class="status healthy">
            <strong>Status:</strong> System is running normally
        </div>
        
        <div class="endpoints">
            <h3>Available Endpoints:</h3>
            <ul>
                <li><a href="/docs">API Documentation</a> - Interactive API docs</li>
                <li><a href="/health">Health Check</a> - System status</li>
                <li><a href="/tasks">Tasks API</a> - View tasks data</li>
            </ul>
        </div>
        
        <div>
            <h3>Quick Actions:</h3>
            <button onclick="window.location.href='/docs'">Open API Docs</button>
            <button onclick="checkHealth()">Check Health</button>
        </div>
        
        <div id="health-result" style="margin-top: 20px;"></div>
    </div>

    <script>
        async function checkHealth() {
            const response = await fetch('/health');
            const data = await response.json();
            document.getElementById('health-result').innerHTML = 
                '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return html_template

@app.get("/app", response_class=HTMLResponse)
async def app_route():
    return html_template

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat(), "service": "RGA TaskDesk"}

@app.get("/tasks")
async def get_tasks():
    return {"tasks": ["Sample task 1", "Sample task 2"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
