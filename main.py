from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from backtester import run_backtest

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/backtest")
async def backtest(interval: str = Form(...), start_date: str = Form(None), end_date: str = Form(None)):
    try:
        results = run_backtest(interval=interval, start_date=start_date, end_date=end_date)
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
