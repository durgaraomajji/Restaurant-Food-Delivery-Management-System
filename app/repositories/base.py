from sqlalchemy.orm import Session
class Repository:
    model=None
    def __init__(self, db:Session): self.db=db
    def get(self, obj_id): return self.db.get(self.model,obj_id)
    def list(self, **filters): return self.db.query(self.model).filter_by(**filters).all()
    def add(self, obj): self.db.add(obj); self.db.flush(); return obj
    def delete(self,obj): self.db.delete(obj)
