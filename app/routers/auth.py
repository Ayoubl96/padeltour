from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import db, schemas, models, tools, oauth2
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(

    tags=["auth"],
)


@router.post("/login", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db.get_db)):
    user = db.query(models.Company).filter(
        user_credentials.username == models.Company.login).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    verify = tools.verify_password(user_credentials.password, user.password)
    if not verify:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = oauth2.create_access_token(data={"user_id":user.id})

    return {"access_token":access_token, "token_type":"bearer"}
