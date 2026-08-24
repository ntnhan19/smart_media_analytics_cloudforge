from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from database import get_db
from models.project import Project
from models.asset import Asset
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from typing import List

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    # Retrieve projects with their asset count
    stmt = select(
        Project, 
        func.count(Asset.id).label('asset_count')
    ).outerjoin(Asset, Project.id == Asset.project_id).group_by(Project.id).order_by(Project.created_at.desc())
    
    result = await db.execute(stmt)
    rows = result.all()
    
    response = []
    for row in rows:
        proj = row[0]
        proj.asset_count = row[1]
        response.append(proj)
        
    return response

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_in: ProjectCreate, db: AsyncSession = Depends(get_db)):
    new_proj = Project(name=project_in.name, description=project_in.description)
    db.add(new_proj)
    await db.commit()
    await db.refresh(new_proj)
    new_proj.asset_count = 0
    return new_proj

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_in: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project_in.name is not None:
        proj.name = project_in.name
    if project_in.description is not None:
        proj.description = project_in.description
        
    await db.commit()
    await db.refresh(proj)
    
    # get asset count
    count_res = await db.execute(select(func.count(Asset.id)).where(Asset.project_id == project_id))
    proj.asset_count = count_res.scalar_one()
    return proj

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Optional: Unlink assets from this project or cascade delete
    await db.execute(Asset.__table__.update().where(Asset.project_id == project_id).values(project_id=None))
        
    await db.delete(proj)
    await db.commit()
    return None
