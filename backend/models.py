from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Prompt(Base):
    """Prompt 主表"""
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, default="")
    content = Column(Text, nullable=False)  # 当前版本内容
    variables = Column(JSON, default=list)  # ["name", "age"]
    tags = Column(JSON, default=list)  # ["code", "review"]
    model = Column(String(100), default="gpt-4")  # 推荐使用的模型
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_version = Column(Integer, default=1)
    
    # 关系
    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")

class PromptVersion(Base):
    """Prompt 版本历史"""
    __tablename__ = "prompt_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False)
    version = Column(Integer, nullable=False)  # 版本号
    content = Column(Text, nullable=False)  # 该版本内容
    variables = Column(JSON, default=list)
    change_message = Column(String(500), default="")  # 变更说明
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    prompt = relationship("Prompt", back_populates="versions")

# 数据库连接
engine = create_engine("sqlite:///./promptvault.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
