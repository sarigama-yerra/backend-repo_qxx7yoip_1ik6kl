import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Video

app = FastAPI(title="Premanand Maharaj Media API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


@app.get("/")
def read_root():
    return {"message": "Premanand Maharaj Media API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Request models
class VideoCreate(Video):
    pass


# Endpoints
@app.post("/api/videos", status_code=201)
def create_video(payload: VideoCreate):
    try:
        vid_id = create_document("video", payload)
        return {"id": vid_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos")
def list_videos(
    q: Optional[str] = Query(None, description="Search by title, tag, or scripture name"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    scripture: Optional[str] = Query(None, description="Filter by scripture name"),
    limit: int = Query(50, ge=1, le=200)
):
    try:
        filt = {}
        if q:
            filt["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}},
                {"scriptures.scripture": {"$regex": q, "$options": "i"}}
            ]
        if platform:
            filt["platform"] = platform
        if scripture:
            filt["scriptures.scripture"] = {"$regex": scripture, "$options": "i"}

        docs = get_documents("video", filt, limit)
        # Serialize ObjectId and datetime
        def serialize(doc):
            doc["id"] = str(doc.pop("_id"))
            for s in doc.get("scriptures", []):
                # keep as-is; pydantic will handle on input, we just return dicts
                pass
            if doc.get("published_at") and hasattr(doc["published_at"], "isoformat"):
                doc["published_at"] = doc["published_at"].isoformat()
            if doc.get("created_at") and hasattr(doc["created_at"], "isoformat"):
                doc["created_at"] = doc["created_at"].isoformat()
            if doc.get("updated_at") and hasattr(doc["updated_at"], "isoformat"):
                doc["updated_at"] = doc["updated_at"].isoformat()
            return doc
        return [serialize(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos/{video_id}")
def get_video(video_id: str):
    try:
        from bson.objectid import ObjectId
        if not ObjectId.is_valid(video_id):
            raise HTTPException(status_code=400, detail="Invalid ID")
        doc = db["video"].find_one({"_id": ObjectId(video_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Not found")
        doc["id"] = str(doc.pop("_id"))
        for k in ["published_at", "created_at", "updated_at"]:
            v = doc.get(k)
            if v and hasattr(v, "isoformat"):
                doc[k] = v.isoformat()
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
def get_schema():
    # Expose schemas for the built-in viewer if needed
    return {"collections": ["video", "playlist"]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
