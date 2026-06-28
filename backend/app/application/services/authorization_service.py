from app.core.exceptions import Forbidden
from app.domain.enums import UserRole


class AuthorizationService:
    """
    Service responsible for verifying User Role Based Access Control (RBAC).
    Decoupled to support permission-based validation hooks in the future.
    """

    def authorize_role(self, user_role: UserRole, required_role: UserRole) -> None:
        """
        Checks if the current user role satisfies the required clearance role.
        ADMIN has global clearance.
        """
        if user_role == UserRole.ADMIN:
            return

        if required_role == UserRole.ADMIN and user_role != UserRole.ADMIN:
            raise Forbidden("Admin clearance is required to execute this operation.")

        if user_role != required_role:
            raise Forbidden(
                "You do not have the required permissions to perform this action."
            )

    def authorize_resource_ownership(
        self, resource_owner_id: str, requesting_user_id: str
    ) -> None:
        """
        Checks if the requesting user owns the target resource.
        """
        if str(resource_owner_id) != str(requesting_user_id):
            raise Forbidden("Access to the requested resource is denied.")
