from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from account import DB, models

account_router = APIRouter()


@account_router.get("/{user_id}")
def get_place(user_id: int, db: Session = Depends(DB.get_db)):
    result = db.query(models.User).filter(models.User.id == user_id).first()

    if result is None:
        return JSONResponse(status_code=404, content={"error": 'No account available here.'})

    return JSONResponse(
        status_code=200,
        content={"status": "OK", "data": result.jsonify()}
    )
