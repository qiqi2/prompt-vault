from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============ Prompt Schemas ============

class PromptBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    content: str = Field(..., min_length=1)
    variables: List[str] = []
    tags: List[str] = []
    model: str = "gpt-4"

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    model: Optional[str] = None
    change_message: str = "Updated"

class PromptResponse(PromptBase):
    id: int
    current_version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============ Version Schemas ============

class VersionBase(BaseModel):
    version: int
    content: str
    variables: List[str] = []
    change_message: str = ""

class VersionResponse(VersionBase):
    id: int
    prompt_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Render Schema ============

class RenderRequest(BaseModel):
    variables: Dict[str, Any] = {}

class RenderResponse(BaseModel):
    rendered_content: str

# ============ Diff Schema ============

class DiffResponse(BaseModel):
    from_version: int
    to_version: int
    diff: str  # 简化：直接返回差异文本
