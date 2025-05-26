import threading
import json
from payloadcomputerdroneprojekt.image_analysis.data_handler import FILENAME
from payloadcomputerdroneprojekt.test.image_analysis.helper import TestCamera
from payloadcomputerdroneprojekt import MissionComputer
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
from os.path import join


app = FastAPI()

# These should be references to your actual data
mission_file_path = "./new_mission_received.json"


config = os.path.join(os.path.dirname(__file__), "config_px4.json")
mission = ""
with open(config) as f:
    config = json.load(f)
port = "udp://:14540"
computer = MissionComputer(config=config, camera=TestCamera, port=port)
computer.initiate(mission)
DATA = computer._image._data_handler._path


@app.get("/found_objects")
async def get_found_objects():
    file_path = join(DATA, FILENAME)
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

api_thread = threading.Thread(target=computer.start, daemon=True)
api_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("start_webserver_gazebo:app", port=6942, reload=False)
