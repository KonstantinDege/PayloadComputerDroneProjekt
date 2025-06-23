import threading
import json
from payloadcomputerdroneprojekt.image_analysis.data_handler \
    import FILENAME, FILENAME_FILTERED
from payloadcomputerdroneprojekt.camera.raspi2 import RaspiCamera
from payloadcomputerdroneprojekt import MissionComputer
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
import os
from os.path import join
from pathlib import Path


app = FastAPI(docs_url=None, redoc_url=None)
static_path = Path(__file__).parent / "../static"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    # Generate the default Swagger UI HTML
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Custom Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

    # Convert the body from bytes to string
    html_content = response.body.decode("utf-8")

    # Inject <link rel="icon"> into the <head>
    html_content = html_content.replace(
        "<head>",
        "<head><link rel='icon' href='/static/favicon.ico' type='image/x-icon'>"
    )

    # Return modified HTML
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/redoc", include_in_schema=False)
async def redoc_docs():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title="Aerosmurf ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(static_path / "favicon.ico")

# These should be references to your actual data
mission_file_path = "./new_mission_received.json"


config = os.path.join(os.path.dirname(__file__), "config_px4.json")
mission = ""
with open(config) as f:
    config = json.load(f)
port = "serial:///dev/ttyAMA0:115200"
computer: MissionComputer = MissionComputer(
    config=config, camera=RaspiCamera, port=port)

try:
    computer.initiate(mission)
except Exception as e:
    print(f"Error initiating mission computer: {e}")
DATA = computer._image._data_handler._path


@app.get("/found_objects")
async def get_found_objects():
    file_path = join(DATA, FILENAME)
    if os.path.exists(file_path):
        return FileResponse(
            file_path, media_type="application/json", filename=FILENAME)
    return HTTPException(status_code=404, detail="Data file not found")


@app.get("/found_objects_filtered")
async def get_filtered_objects():
    computer._image.get_filtered_objs()
    file_path = join(DATA, FILENAME_FILTERED)
    print(file_path)
    if os.path.exists(file_path):
        return FileResponse(
            file_path, media_type="application/json", filename=FILENAME)
    return HTTPException(status_code=404, detail="Data file not found")


@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join(DATA, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTTPException(status_code=404, detail="Image not found")


@app.post("/mission")
async def upload_mission(file: UploadFile = File(...)):
    with open(mission_file_path, "wb") as f:
        f.write(await file.read())
    await computer.new_mission(mission_file_path)
    return {"detail": "Mission file uploaded successfully"}


@app.delete("/data_reset")
async def reset_data():
    computer._image._data_handler.reset_data()
    return {"detail": "Data reset successfully"}


@app.get("/log")
async def get_log():
    log_file_path = "flight.log"
    if os.path.exists(log_file_path):
        return FileResponse(
            log_file_path, media_type="text/plain", filename=log_file_path)
    return HTTPException(status_code=404, detail="Log file not found")


api_thread = threading.Thread(target=computer.start, daemon=True)
api_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("start_webserver_raspi:app", port=4269, reload=False)
