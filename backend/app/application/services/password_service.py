import re
import bcrypt
from app.core.exceptions import WeakPassword

class PasswordService:
    """
    Service responsible for enforcing password strength policies,
    hashing, and verifying passwords using bcrypt.
    """
    
    def validate_password_strength(self, password: str) -> None:
        """
        Enforces secure password criteria:
        - Minimum length of 8 characters.
        - Contains at least one uppercase letter.
        - Contains at least one lowercase letter.
        - Contains at least one numeric digit.
        - Contains at least one special character (e.g. @, $, !, %, *, ?, &).
        """
        if len(password) < 8:
            raise WeakPassword("Password must be at least 8 characters long.")
            
        if not re.search(r"[A-Z]", password):
            raise WeakPassword("Password must contain at least one uppercase letter.")
            
        if not re.search(r"[a-z]", password):
            raise WeakPassword("Password must contain at least one lowercase letter.")
            
        if not re.search(r"\d", password):
            raise WeakPassword("Password must contain at least one numeric digit.")
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise WeakPassword("Password must contain at least one special character.")

    def hash_password(self, password: str) -> str:
        """
        Hashes password using bcrypt with a work factor of 12.
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies plain text password against the hashed representation safely.
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), 
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False
