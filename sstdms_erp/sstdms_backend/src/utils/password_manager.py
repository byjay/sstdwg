# password_manager.py

import hashlib
import secrets
import bcrypt
from typing import Optional

class PasswordManager:
    """Enhanced password management system with secure hashing and validation."""
    
    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt for password hashing."""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a password using bcrypt with optional salt.
        Returns tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = PasswordManager.generate_salt()
        
        # Combine password with salt
        password_with_salt = password + salt
        
        # Use bcrypt for secure hashing
        hashed = bcrypt.hashpw(password_with_salt.encode('utf-8'), bcrypt.gensalt())
        
        return hashed.decode('utf-8'), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """Verify a password against its hash."""
        try:
            password_with_salt = password + salt
            return bcrypt.checkpw(password_with_salt.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            print(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def is_strong_password(password: str) -> tuple[bool, list[str]]:
        """
        Check if password meets security requirements.
        Returns tuple of (is_strong, list_of_issues)
        """
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Generate a secure random password."""
        import string
        
        # Ensure we have at least one character from each required category
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")
        ]
        
        # Fill the rest with random characters
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)

# Example usage and testing
if __name__ == '__main__':
    pm = PasswordManager()
    
    # Test password strength
    test_passwords = ["weak", "StrongPass123!", "short"]
    for pwd in test_passwords:
        is_strong, issues = pm.is_strong_password(pwd)
        print(f"Password '{pwd}': Strong={is_strong}, Issues={issues}")
    
    # Test password hashing and verification
    password = "TestPassword123!"
    hashed, salt = pm.hash_password(password)
    print(f"Original: {password}")
    print(f"Hashed: {hashed}")
    print(f"Salt: {salt}")
    
    # Verify password
    is_valid = pm.verify_password(password, hashed, salt)
    print(f"Verification: {is_valid}")
    
    # Test with wrong password
    is_valid_wrong = pm.verify_password("WrongPassword", hashed, salt)
    print(f"Wrong password verification: {is_valid_wrong}")
    
    # Generate secure password
    secure_pwd = pm.generate_secure_password()
    print(f"Generated secure password: {secure_pwd}")

