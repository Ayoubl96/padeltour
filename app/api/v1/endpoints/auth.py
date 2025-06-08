from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token
from app.db.database import get_db
from app.models.company import Company
from app.utils.security import verify_password
from app.utils.logging_utils import log_user_action, log_error, log_database_operation
from app.core.logging_config import get_logger
# Enhanced business event logging (optional)
from grafana.enhanced_middleware_v2 import log_enhanced_business_event

router = APIRouter()
logger = get_logger("padeltour.auth")


@router.post("/login", response_model=schemas.Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None
):
    try:
        # Log login attempt
        log_user_action(
            "padeltour.auth",
            "login_attempt",
            request=request,
            extra_data={"username": user_credentials.username}
        )
        
        user = db.query(Company).filter(
            user_credentials.username == Company.login
        ).first()

        if not user:
            # Log failed login - user not found
            log_error(
                "padeltour.auth",
                f"Login failed - user not found: {user_credentials.username}",
                error_type="authentication_error",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid credentials"
            )

        is_valid = verify_password(user_credentials.password, user.password)
        if not is_valid:
            # Log failed login - invalid password
            log_error(
                "padeltour.auth",
                f"Login failed - invalid password for user: {user_credentials.username}",
                error_type="authentication_error",
                request=request,
                user_id=user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid credentials"
            )

        access_token = create_access_token(data={"user_id": user.id})
        refresh_token = create_refresh_token(data={"user_id": user.id})

        # Log successful login
        log_user_action(
            "padeltour.auth",
            "login_success",
            user_id=user.id,
            request=request,
            extra_data={"username": user_credentials.username}
        )
        
        # Enhanced business event logging for better analytics
        log_enhanced_business_event(
            "user_login",
            user_id=user.id,
            company_id=user.id,  # Assuming company is the user in this case
            additional_data={
                "username": user_credentials.username,
                "login_method": "password"
            },
            request=request
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        log_error(
            "padeltour.auth",
            f"Unexpected error during login: {str(e)}",
            error_type="system_error",
            request=request,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    refresh_request: schemas.RefreshRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    try:
        # Log token refresh attempt
        log_user_action(
            "padeltour.auth",
            "token_refresh_attempt",
            request=request
        )
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
        token_data = verify_refresh_token(refresh_request.refresh_token, credentials_exception)
        
        # Log database query for user
        log_database_operation(
            "padeltour.auth",
            "SELECT",
            "companies",
            record_id=token_data.id,
            request=request
        )
        
        user = db.query(Company).filter(Company.id == token_data.id).first()
        if not user:
            # Log user not found during refresh
            log_error(
                "padeltour.auth",
                f"Token refresh failed - user not found: {token_data.id}",
                error_type="authentication_error",
                request=request,
                user_id=token_data.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        access_token = create_access_token(data={"user_id": user.id})
        refresh_token = create_refresh_token(data={"user_id": user.id})
        
        # Log successful token refresh
        log_user_action(
            "padeltour.auth",
            "token_refresh_success",
            user_id=user.id,
            request=request
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        log_error(
            "padeltour.auth",
            f"Unexpected error during token refresh: {str(e)}",
            error_type="system_error",
            request=request,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 