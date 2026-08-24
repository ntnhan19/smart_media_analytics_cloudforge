from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models.saved_search import SavedSearch
from schemas.saved_search import SavedSearchCreate, SavedSearchResponse
from typing import List

router = APIRouter(prefix="/api/v1/saved-searches", tags=["saved-searches"])

@router.get("/", response_model=List[SavedSearchResponse])
async def list_saved_searches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SavedSearch).order_by(SavedSearch.created_at.desc()))
    return result.scalars().all()

@router.post("/", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(search_in: SavedSearchCreate, db: AsyncSession = Depends(get_db)):
    new_search = SavedSearch(query_text=search_in.query_text)
    db.add(new_search)
    await db.commit()
    await db.refresh(new_search)
    return new_search

@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(search_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SavedSearch).where(SavedSearch.id == search_id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    await db.delete(search)
    await db.commit()
    return None
