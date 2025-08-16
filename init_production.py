# init_production.py - Initialize database for production
import os
import sys
from app import app, db, Project

def init_production_database():
    """Initialize database for production deployment"""
    print("🚀 Starting production database initialization...")
    
    with app.app_context():
        try:
            # Create all tables
            print("📝 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if we need sample data
            if Project.query.count() == 0:
                print("📦 No projects found, initializing with sample data...")
                from init_db import init_database
                init_database()
                print("✅ Sample data initialized successfully")
            else:
                print("📊 Database already contains data, skipping sample data initialization")
                
        except Exception as e:
            print(f"❌ Error during database initialization: {e}")
            sys.exit(1)
    
    print("🎉 Production database initialization completed successfully!")

if __name__ == "__main__":
    init_production_database()