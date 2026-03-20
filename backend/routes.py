from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import re
from datetime import datetime

from models import get_db, Prompt, PromptVersion
from schemas import (
    PromptCreate, PromptUpdate, PromptResponse,
    VersionResponse, RenderRequest, RenderResponse, DiffResponse
)

router = APIRouter(prefix="/prompts", tags=["prompts"])

def extract_variables(content: str) -> List[str]:
    """从内容中提取 {{variable}} 格式的变量"""
    pattern = r'\{\{(\w+)\}\}'
    return list(set(re.findall(pattern, content)))

def create_version(db: Session, prompt: Prompt, new_content: str, change_message: str = ""):
    """创建新版本"""
    # 检查内容是否真的变了
    if prompt.content == new_content:
        return None
    
    # 创建新版本记录
    version = PromptVersion(
        prompt_id=prompt.id,
        version=prompt.current_version,
        content=prompt.content,
        variables=prompt.variables,
        change_message=change_message
    )
    db.add(version)
    
    # 更新 prompt
    prompt.content = new_content
    prompt.variables = extract_variables(new_content)
    prompt.current_version += 1
    prompt.updated_at = datetime.utcnow()
    
    return version

@router.get("", response_model=List[PromptResponse])
def list_prompts(
    skip: int = 0,
    limit: int = 100,
    tag: str = None,
    db: Session = Depends(get_db)
):
    """获取所有 Prompts"""
    query = db.query(Prompt)
    if tag:
        query = query.filter(Prompt.tags.contains([tag]))
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    """创建新 Prompt"""
    # 检查名称是否已存在
    existing = db.query(Prompt).filter(Prompt.name == prompt.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Prompt name already exists")
    
    # 提取变量
    variables = extract_variables(prompt.content)
    
    db_prompt = Prompt(
        name=prompt.name,
        description=prompt.description,
        content=prompt.content,
        variables=variables,
        tags=prompt.tags,
        model=prompt.model
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    
    # 创建初始版本
    create_version(db, db_prompt, prompt.content, "Initial version")
    db.commit()
    
    return db_prompt

@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """获取单个 Prompt"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@router.put("/{prompt_id}", response_model=PromptResponse)
def update_prompt(
    prompt_id: int,
    prompt_update: PromptUpdate,
    db: Session = Depends(get_db)
):
    """更新 Prompt（自动创建版本）"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # 更新字段
    update_data = prompt_update.model_dump(exclude_unset=True)
    change_message = update_data.pop("change_message", "Updated")
    
    new_content = update_data.get("content", prompt.content)
    
    # 如果内容变了，创建新版本
    if "content" in update_data and update_data["content"] != prompt.content:
        create_version(prompt, prompt, new_content, change_message)
    
    for key, value in update_data.items():
        if value is not None:
            setattr(prompt, key, value)
    
    prompt.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prompt)
    
    return prompt

@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """删除 Prompt"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    db.delete(prompt)
    db.commit()
    return None

@router.get("/{prompt_id}/versions", response_model=List[VersionResponse])
def get_versions(prompt_id: int, db: Session = Depends(get_db)):
    """获取版本历史"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    versions = db.query(PromptVersion).filter(
        PromptVersion.prompt_id == prompt_id
    ).order_by(PromptVersion.version.desc()).all()
    
    # 加入当前版本
    all_versions = [
        VersionResponse(
            id=0,
            prompt_id=prompt_id,
            version=prompt.current_version,
            content=prompt.content,
            variables=prompt.variables,
            change_message="Current",
            created_at=prompt.updated_at
        )
    ]
    all_versions.extend([
        VersionResponse(
            id=v.id,
            prompt_id=v.prompt_id,
            version=v.version,
            content=v.content,
            variables=v.variables,
            change_message=v.change_message,
            created_at=v.created_at
        ) for v in versions
    ])
    
    return all_versions

@router.post("/{prompt_id}/rollback/{version}")
def rollback_version(
    prompt_id: int,
    version: int,
    db: Session = Depends(get_db)
):
    """回滚到指定版本"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if version == prompt.current_version:
        raise HTTPException(status_code=400, detail="Already at this version")
    
    # 查找目标版本
    target_version = db.query(PromptVersion).filter(
        PromptVersion.prompt_id == prompt_id,
        PromptVersion.version == version
    ).first()
    
    if not target_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # 创建新版本记录当前内容，然后回滚
    create_version(prompt, prompt, target_version.content, f"Rollback to v{version}")
    db.commit()
    
    return {"message": f"Rolled back to version {version}", "current_version": prompt.current_version}

@router.post("/{prompt_id}/render", response_model=RenderResponse)
def render_prompt(prompt_id: int, request: RenderRequest, db: Session = Depends(get_db)):
    """渲染 Prompt（替换变量）"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    rendered = prompt.content
    for key, value in request.variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    
    return RenderResponse(rendered_content=rendered)

@router.get("/{prompt_id}/diff")
def diff_versions(
    prompt_id: int,
    from_version: int,
    to_version: int,
    db: Session = Depends(get_db)
):
    """对比两个版本的差异"""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # 获取 from 版本内容
    if from_version == prompt.current_version:
        from_content = prompt.content
    else:
        from_ver = db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == from_version
        ).first()
        if not from_ver:
            raise HTTPException(status_code=404, detail="From version not found")
        from_content = from_ver.content
    
    # 获取 to 版本内容
    if to_version == prompt.current_version:
        to_content = prompt.content
    else:
        to_ver = db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == to_version
        ).first()
        if not to_ver:
            raise HTTPException(status_code=404, detail="To version not found")
        to_content = to_ver.content
    
    # 简单的 diff（实际可以用 difflib）
    from_lines = from_content.split('\n')
    to_lines = to_content.split('\n')
    
    diff_lines = []
    for i, (f, t) in enumerate(zip(from_lines, to_lines)):
        if f != t:
            diff_lines.append(f"Line {i+1}:")
            diff_lines.append(f"  - {f}")
            diff_lines.append(f"  + {t}")
    
    if len(from_lines) != len(to_lines):
        diff_lines.append(f"\n... ({len(to_lines) - len(from_lines)} lines)")
    
    return DiffResponse(
        from_version=from_version,
        to_version=to_version,
        diff="\n".join(diff_lines) if diff_lines else "No changes"
    )
