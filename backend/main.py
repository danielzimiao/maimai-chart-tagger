import os
import json
import zipfile
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import shutil

from parser import parse
from analyzer import analyze
from database import find_similar, get_songs_by_tag

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_chart(file: UploadFile = File(...)):
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    if suffix not in (".txt", ".zip", ".axlv"):
        raise HTTPException(status_code=422, detail={"error": "Unsupported file type"})

    tmpdir = None
    tmpfile = None

    try:
        if suffix == ".txt":
            # Save directly to a temp file
            fd, tmpfile = tempfile.mkstemp(suffix=".txt")
            try:
                with os.fdopen(fd, "wb") as fh:
                    shutil.copyfileobj(file.file, fh)
            except Exception:
                os.close(fd)
                raise
            maidata_path = tmpfile
        else:
            # .zip or .axlv — extract and find maidata.txt
            tmpdir = tempfile.mkdtemp()
            zip_fd, zip_tmp = tempfile.mkstemp(suffix=suffix)
            try:
                with os.fdopen(zip_fd, "wb") as fh:
                    shutil.copyfileobj(file.file, fh)
            except Exception:
                os.close(zip_fd)
                raise

            try:
                with zipfile.ZipFile(zip_tmp, "r") as zf:
                    zf.extractall(tmpdir)
            finally:
                os.unlink(zip_tmp)

            maidata_path = str(next(Path(tmpdir).rglob("maidata.txt")))

        try:
            features = parse(maidata_path)
            result = analyze(features)
            tags = result.get("tags", [])
            difficulty = result.get("difficulty")
            similar_songs = find_similar(tags, limit=3)
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"error": str(exc)},
            )

        return {
            "difficulty": difficulty,
            "tags": tags,
            "similar_songs": similar_songs,
        }

    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)
        if tmpfile is not None:
            try:
                os.unlink(tmpfile)
            except OSError:
                pass


@app.get("/tags/{tag_name}")
def songs_by_tag(tag_name: str):
    songs = get_songs_by_tag(tag_name)
    return {"tag": tag_name, "songs": songs}
