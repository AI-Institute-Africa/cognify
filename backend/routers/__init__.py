"""Routers package"""
from .auth import router as auth_router
from .courses import router as courses_router
from .students import router as students_router
from .dashboard import router as dashboard_router

__all__ = [
    'auth_router',
    'courses_router', 
    'students_router',
    'dashboard_router',
]
