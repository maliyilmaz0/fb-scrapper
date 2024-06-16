from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from db.sql import INSERT_PROCESS, GET_PROCESS, GET_RESULTS, GET_RESULTS_BY_ID
from models.posts import Posts
from db.db import get_cursor

router = APIRouter()

@router.get("/")
async def results():
    try:
        cursor = get_cursor(dictionary=True)
        cursor.execute(GET_RESULTS)
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



@router.get("/{id}")
async def get_post(id: int):
    try:
        cursor = get_cursor(dictionary=True)
        cursor.execute(GET_RESULTS_BY_ID, (id,))
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
