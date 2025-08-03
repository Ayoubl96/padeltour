from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.company import Company
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardResponse

router = APIRouter()


@router.get("/overview", response_model=DashboardResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_user)
):
    """
    Get comprehensive dashboard overview with all key metrics and analytics
    
    Returns:
    - Tournament management overview (active, upcoming, completed tournaments)
    - Real-time tournament progress (completion %, stage progress, top couples)
    - Match & court analytics (matches per day, court efficiency, peak hours)
    - Player & couple performance (most active players, best couples, level distribution)
    - Operational dashboard (upcoming matches, conflicts, deadlines, alerts)
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard_data = dashboard_service.get_dashboard_data(current_company.id)
        
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating dashboard data: {str(e)}"
        )