import uuid
from typing import Dict, Optional
from fastapi import APIRouter, Depends, Request, Response, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.dtos import (
    UserRegisterRequest,
    UserLoginRequest,
    LoginResponse,
    UserResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    UserUpdateRequest
)
from app.api.deps import (
    get_auth_service,
    get_token_service,
    get_current_user,
    get_user_repository
)
from app.domain.models import User
from app.application.services.auth_service import AuthService
from app.application.services.token_service import TokenService
from app.domain.repositories.user_repository import IUserRepository
from app.core.exceptions import ValidationError, Unauthorized
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Sets secure HTTP-Only cookie for refresh token rotation."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "prod",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/v1/auth" # Restrict cookie transmission path for security
    )

def _clear_refresh_cookie(response: Response) -> None:
    """Clears refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth"
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegisterRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"

    try:
        return auth_service.register_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            ip_address=ip_address,
            device=user_agent
        )
    except Exception as e:
        import traceback
        print("\n" + "=" * 80)
        print("REGISTRATION ERROR")
        print("=" * 80)
        traceback.print_exc()
        print("=" * 80 + "\n")
        raise

@router.post("/login", response_model=LoginResponse)
def login(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    access_token, refresh_token, _ = auth_service.login_user(
        email=payload.email,
        password=payload.password,
        device_name=payload.device_name,
        browser=payload.browser,
        operating_system=payload.operating_system,
        ip_address=ip_address,
        user_agent_str=user_agent
    )
    
    # Securely set refresh token cookie
    _set_refresh_cookie(response, refresh_token)
    return LoginResponse(access_token=access_token)

# Enforce compatibility with Swagger OAuth2 standard flow using form data
@router.post("/oauth2-login", response_model=LoginResponse, include_in_schema=False)
def oauth2_login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    access_token, refresh_token, _ = auth_service.login_user(
        email=form_data.username,
        password=form_data.password,
        device_name="OAuth2 Client",
        browser="Swagger UI",
        operating_system="Unknown",
        ip_address=ip_address,
        user_agent_str=user_agent
    )
    _set_refresh_cookie(response, refresh_token)
    return LoginResponse(access_token=access_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    if refresh_token:
        try:
            # Extract token family claim to revoke session
            payload = token_service.verify_access_token(request.headers.get("Authorization").split(" ")[1])
            token_family = uuid.UUID(payload["token_family"])
            auth_service.logout_user(
                user_id=current_user.id,
                token_family=token_family,
                ip_address=ip_address,
                device=user_agent
            )
        except Exception:
            pass
            
    _clear_refresh_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    auth_service.logout_all_sessions(
        user_id=current_user.id,
        ip_address=ip_address,
        device=user_agent
    )
    _clear_refresh_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/refresh", response_model=LoginResponse)
def refresh_token_route(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    token_service: TokenService = Depends(get_token_service)
):
    if not refresh_token:
        raise Unauthorized("Refresh token cookie missing.")
        
    # Rotate token family
    new_access, new_refresh = token_service.rotate_refresh_token(refresh_token)
    
    # Update cookie with rotated token representation
    _set_refresh_cookie(response, new_refresh)
    return LoginResponse(access_token=new_access)

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    auth_service.change_password(
        user_id=current_user.id,
        old_password=payload.old_password,
        new_password=payload.new_password,
        ip_address=ip_address,
        device=user_agent
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    auth_service.forgot_password(
        email=payload.email,
        ip_address=ip_address,
        device=user_agent
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    auth_service.reset_password(
        token=payload.token,
        new_password=payload.new_password,
        ip_address=ip_address,
        device=user_agent
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("User-Agent") or "Unknown"
    
    auth_service.verify_email(
        token=payload.token,
        ip_address=ip_address,
        device=user_agent
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    user_repo: IUserRepository = Depends(get_user_repository)
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
        current_user.updated_at = datetime.utcnow()
        updated = user_repo.update(current_user)
        # Flush db transaction session context
        user_repo.db.commit() # Repository has self.db bound inside constructor
        return updated
    return current_user
