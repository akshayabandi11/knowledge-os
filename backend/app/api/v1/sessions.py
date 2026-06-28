import uuid
from typing import List
from fastapi import APIRouter, Depends, status, Response

from app.api.v1.dtos import SessionResponse
from app.api.deps import get_session_service, get_current_user
from app.domain.models import User
from app.application.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Sessions Management"])

@router.get("", response_model=List[SessionResponse])
def get_sessions(
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Returns a list of all active non-revoked sessions belonging to the current user.
    """
    return session_service.get_active_sessions(current_user.id)

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def terminate_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Terminates a specific login session. Users can only revoke their own sessions.
    """
    session_service.revoke_session(session_id=session_id, user_id=current_user.id)
    # Commit changes on DB transaction boundaries
    session_service.session_repo.db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
