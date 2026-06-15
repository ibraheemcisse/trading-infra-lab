#!/usr/bin/env python3
"""
Chaos Control Panel - Web UI for triggering chaos tests
FastAPI endpoint to inject/recover failures
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import subprocess
import asyncio

app = FastAPI(title="Trading Lab Chaos Control")

# Available chaos tests
CHAOS_TESTS = {
    "01": "Feed Blackout",
    "02": "Latency Injection",
    "04": "Consumer Crash",
    "05": "Kafka Container Stop",
}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Control panel UI"""
    buttons = "".join([
        f'<button onclick="inject(\'{test_id}\')">{CHAOS_TESTS[test_id]} (Inject)</button>'
        f'<button onclick="recover(\'{test_id}\')">{CHAOS_TESTS[test_id]} (Recover)</button><br>'
        for test_id in CHAOS_TESTS.keys()
    ])
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Lab - Chaos Control Panel</title>
        <style>
            body {{ font-family: monospace; padding: 20px; background: #1e1e1e; color: #00ff00; }}
            button {{ padding: 10px 20px; margin: 5px; background: #333; border: 1px solid #00ff00; color: #00ff00; cursor: pointer; }}
            button:hover {{ background: #00ff00; color: #1e1e1e; }}
            #log {{ background: #0a0a0a; padding: 10px; margin-top: 20px; height: 300px; overflow-y: auto; border: 1px solid #00ff00; }}
            .success {{ color: #00ff00; }}
            .error {{ color: #ff0000; }}
        </style>
    </head>
    <body>
        <h1>⚡ Trading Lab Chaos Control Panel</h1>
        <div>
            {buttons}
        </div>
        <div id="log"></div>
        <script>
            const log = document.getElementById('log');
            function log_msg(msg, cls='') {{
                const line = document.createElement('div');
                line.textContent = msg;
                if (cls) line.className = cls;
                log.appendChild(line);
                log.scrollTop = log.scrollHeight;
            }}
            async function inject(test_id) {{
                log_msg(`[INJECT] Starting chaos {test_id}...`);
                const res = await fetch(`/api/inject/${{test_id}}`);
                const data = await res.json();
                log_msg(`[RESULT] ${{data.message}}`, data.status === 'success' ? 'success' : 'error');
            }}
            async function recover(test_id) {{
                log_msg(`[RECOVER] Recovering chaos ${{test_id}}...`);
                const res = await fetch(`/api/recover/${{test_id}}`);
                const data = await res.json();
                log_msg(`[RESULT] ${{data.message}}`, data.status === 'success' ? 'success' : 'error');
            }}
        </script>
    </body>
    </html>
    """

@app.get("/api/inject/{test_id}")
async def inject_chaos(test_id: str):
    """Trigger chaos injection"""
    if test_id not in CHAOS_TESTS:
        raise HTTPException(status_code=404, detail="Unknown test")
    
    try:
        result = subprocess.run(
            ["python3", f"chaos/{test_id}_*.py", "inject"],
            cwd="/home/ubuntu/trading-infra-lab",
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "message": result.stdout + result.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/recover/{test_id}")
async def recover_chaos(test_id: str):
    """Trigger chaos recovery"""
    if test_id not in CHAOS_TESTS:
        raise HTTPException(status_code=404, detail="Unknown test")
    
    try:
        result = subprocess.run(
            ["python3", f"chaos/{test_id}_*.py", "recover"],
            cwd="/home/ubuntu/trading-infra-lab",
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "message": result.stdout + result.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
