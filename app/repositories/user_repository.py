from .base import Repository
from ..models.models import User
class UserRepository(Repository):
    model=User
    def by_email(self,email): return self.db.query(User).filter_by(email=email).first()
