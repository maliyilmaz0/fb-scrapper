from pydantic import BaseModel



"""
    name varchar(255),
    status int default 1,
    start_time timestamp,
    end_time timestamp,
    items varchar[]
"""


class Posts(BaseModel):
    name: str
    items: list[str]
