import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from run_simulation import build_dummy_simulation, build_rl_simulation
from regulator.detector import LambdaMonitor

app = FastAPI(title="ECHO Antitrust Simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationConfig(BaseModel):
    mode: str
    rounds: int

@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard/index.html")

app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.websocket("/ws/simulate")
async def simulate_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Wait for the config from the client
        config_text = await websocket.receive_text()
        config = json.loads(config_text)
        mode = config.get("mode", "dummy")
        n_rounds = config.get("rounds", 50)
        
        print(f"Starting {mode} simulation for {n_rounds} rounds")
        
        if mode == "rl":
            engine, _ = build_rl_simulation(n_rounds)
        else:
            engine, _ = build_dummy_simulation(n_rounds)
            
        monitor = LambdaMonitor()
        
        # Send benchmarks before starting
        benchmarks = {
            "type": "benchmarks",
            "nash_price": engine.benchmarks.nash_price,
            "monopoly_price": engine.benchmarks.monopoly_price,
            "price_floor": engine.price_floor,
            "price_ceiling": engine.price_ceiling
        }
        await websocket.send_text(json.dumps(benchmarks))
        
        # Run simulation round-by-round and stream
        for round_num in range(1, n_rounds + 1):
            record = engine._run_one_round(round_num)
            engine.records.append(record)
            engine.price_history.append(record.prices)
            engine.profit_history.append(record.profits)
            
            # Let agents learn if they are RL agents
            if mode == "rl":
                # Give feedback to agents
                from agents.base_agent import Observation
                for i, agent in enumerate(engine.agents):
                    if hasattr(agent, "learn"):
                        obs = Observation(
                            round_number=round_num,
                            firm_id=agent.firm_id,
                            marginal_cost=float(engine.demand_model.costs[0]),
                            price_floor=engine.price_floor,
                            price_ceiling=engine.price_ceiling,
                            price_history=engine.price_history,
                            profit_history=engine.profit_history,
                        )
                        agent.learn(obs, record.prices, record.profits[i])

            alerts = monitor.observe(record.round_number, record.collusion_index)
            
            payload = {
                "type": "round",
                "round": record.round_number,
                "prices": record.prices,
                "avg_price": record.avg_price,
                "lambda": record.collusion_index,
                "alerts": [{"type": a.alert_type.replace('lambda_', ''), "detail": a.detail} for a in alerts]
            }
            
            # Send updates. If running a long RL simulation (10k+ rounds),
            # batch updates to avoid overloading the websocket.
            if mode == "rl" and n_rounds >= 1000:
                if round_num % 10 == 0 or round_num == n_rounds:
                    await websocket.send_text(json.dumps(payload))
                    # yield control to event loop so websocket can flush
                    await asyncio.sleep(0.001)
            else:
                await websocket.send_text(json.dumps(payload))
                # Add a small delay for dummy agents so it looks animated, 
                # instead of finishing instantly
                await asyncio.sleep(0.05)

        summary = engine.summary()
        await websocket.send_text(json.dumps({"type": "summary", "data": summary}))
        print("Simulation complete.")

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Error during simulation: {e}")
        await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))

@app.get("/api/validation")
def get_validation_data():
    report_path = os.path.join("analysis", "data", "validation_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            return json.load(f)
    return {"error": "Validation report not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
