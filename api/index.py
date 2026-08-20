import sys
import os

# Add api directory to sys.path for Vercel runtime
sys.path.append(os.path.dirname(__file__))

from main import handler, DashboardProxyHandler

# Export handler for Vercel Serverless Functions
__all__ = ['handler', 'DashboardProxyHandler']
