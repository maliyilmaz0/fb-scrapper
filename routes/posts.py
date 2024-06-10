from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from db.sql import INSERT_PROCESS, GET_PROCESS
from models.posts import Posts
from db.db import get_cursor

router = APIRouter()


@router.get("/")
async def posts():
    try:
        cursor = get_cursor(dictionary=True)
        cursor.execute(GET_PROCESS)
        result = cursor.fetchall()
        response = dict(status="success", data=jsonable_encoder(result))
        return JSONResponse(
            status_code=200,
            content=response
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error: {str(e)}"}
        )


@router.post("/")
async def create_post(data: Posts):
    try:
        cursor = get_cursor(dictionary=True)
        cursor.execute(
            INSERT_PROCESS,
            (data.name, data.items)
        )
        return JSONResponse(
            status_code=200,
            content={"message": f"Process {data.name} created successfully!"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error: {str(e)}"}
        )
