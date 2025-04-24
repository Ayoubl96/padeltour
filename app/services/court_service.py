from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.court import Court
from app.models.company import Company


class CourtService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_court(self, name: str, images: List[str], company_id: int) -> Court:
        """Create a new court for a company"""
        new_court = Court(
            name=name,
            images=images,
            company_id=company_id
        )
        
        self.db.add(new_court)
        self.db.commit()
        self.db.refresh(new_court)
        
        return new_court
    
    def get_court_by_id(self, court_id: int, company_id: int) -> Court:
        """Get a court by ID with company verification"""
        court = self.db.query(Court).filter(Court.id == court_id).first()
        
        if not court:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
        
        if court.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this court")
        
        return court
    
    def update_court(self, court_id: int, company_id: int, **update_data) -> Court:
        """Update court details"""
        court = self.get_court_by_id(court_id, company_id)
        
        # Apply updates
        for key, value in update_data.items():
            if hasattr(court, key) and value is not None:
                setattr(court, key, value)
        
        self.db.commit()
        self.db.refresh(court)
        
        return court
    
    def delete_court(self, court_id: int, company_id: int) -> None:
        """Delete a court"""
        court = self.get_court_by_id(court_id, company_id)
        
        self.db.delete(court)
        self.db.commit()
        
        return None
    
    def get_all_courts(self, company_id: int) -> List[Court]:
        """Get all courts for a company"""
        courts = self.db.query(Court).filter(Court.company_id == company_id).all()
        return courts 