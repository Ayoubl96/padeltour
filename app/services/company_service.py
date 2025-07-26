from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.company import Company
from app.utils.security import hash_password


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_company(self, email: str, password: str, name: str, address: str, phone_number: str, vat_number: str) -> Company:
        """Create a new company account"""
        # Check if email is already registered
        existing_company = self.db.query(Company).filter(Company.email == email).first()
        if existing_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Create new company
        new_company = Company(
            email=email,
            password=hashed_password,
            name=name,
            address=address,
            phone_number=phone_number,
            vat_number=vat_number
        )
        
        self.db.add(new_company)
        self.db.commit()
        self.db.refresh(new_company)
        
        return new_company
    
    def get_company_by_id(self, company_id: int) -> Company:
        """Get company by ID"""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        return company
    
    def get_company_by_login(self, login: str) -> Company:
        """Get company by login"""
        company = self.db.query(Company).filter(Company.login == login).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with login: {login} not found"
            )
        return company
    
    def get_all_companies(self) -> List[Company]:
        """Get all companies"""
        return self.db.query(Company).all()
    
    def update_company(self, company_id: int, **kwargs) -> Company:
        """Update company details"""
        company = self.get_company_by_id(company_id)
        
        # Update fields
        for key, value in kwargs.items():
            if key == 'password' and value:
                value = hash_password(value)
            if hasattr(company, key) and value is not None:
                setattr(company, key, value)
        
        self.db.commit()
        self.db.refresh(company)
        
        return company 