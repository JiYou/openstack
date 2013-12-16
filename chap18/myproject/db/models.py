from nova.db.sqlalchemy.models import BASE, NovaBase
from sqlalchemy import Column, Integer, String, Float

class MyProjectHost(BASE, NovaBase):
    __tablename__ = 'myproject_hosts'
    id = Column(Integer, primary_key=True)
    host_name = Column(String(36))
    cpu_usage = Column(Float())
    
