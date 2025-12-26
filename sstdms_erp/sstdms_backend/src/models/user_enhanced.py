# user_enhanced.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class UserEnhanced(Base):
    __tablename__ = 'users_enhanced'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    role = Column(String, default='user') # New field for role-based access control

    def __repr__(self):
        return f"<UserEnhanced(username='{self.username}', email='{self.email}', role='{self.role}')>"

# Example of how to use this model (for demonstration, not part of the actual system)
if __name__ == '__main__':
    engine = create_engine('sqlite:///test_enhanced_users.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Example user creation
    new_user = UserEnhanced(username='testuser_a', hashed_password='hashed_password_a', email='test_a@example.com', role='admin')
    session.add(new_user)
    session.commit()

    print(f"Created user: {new_user}")

    # Query user
    user = session.query(UserEnhanced).filter_by(username='testuser_a').first()
    print(f"Queried user: {user}")

    session.close()


