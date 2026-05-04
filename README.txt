================================================================================
                    TEAM TASK MANAGER - ETHARA AI ASSESSMENT
================================================================================

PROJECT OVERVIEW
--------------------------------------------------------------------------------
A full-stack web application for team task management with role-based access 
control (Admin/Member), project management, task tracking, and dashboard 
analytics.

LIVE APPLICATION URL
--------------------------------------------------------------------------------
https://team-task-manager-ethara-ai.up.railway.app

GITHUB REPOSITORY
--------------------------------------------------------------------------------
https://github.com/Rohini-Koli9/team-task-manager.git

TECH STACK
--------------------------------------------------------------------------------
- Backend: Python + Flask
- Database: PostgreSQL (Railway)
- Authentication: JWT (JSON Web Tokens)
- Frontend: HTML + CSS + JavaScript (Vanilla)
- Deployment: Railway

KEY FEATURES
--------------------------------------------------------------------------------
✓ User Authentication (Signup/Login with JWT)
✓ Project Management (Create, Edit, Delete projects)
✓ Role-Based Access Control (Admin/Member roles)
✓ Task Management (Create, Assign, Track status)
✓ Dashboard with Statistics and Overdue Tasks
✓ RESTful API Architecture
✓ Responsive Design

API ENDPOINTS
--------------------------------------------------------------------------------
Authentication:
  POST /api/auth/register     - User registration
  POST /api/auth/login        - User login
  GET  /api/auth/me           - Get current user

Projects:
  GET  /api/projects          - List user's projects
  POST /api/projects          - Create new project
  GET  /api/projects/<id>     - Get project details
  PUT  /api/projects/<id>     - Update project
  DELETE /api/projects/<id>   - Delete project

Tasks:
  GET  /api/projects/<id>/tasks     - List project tasks
  POST /api/projects/<id>/tasks     - Create task
  GET  /api/tasks/<id>              - Get task details
  PUT  /api/tasks/<id>              - Update task
  DELETE /api/tasks/<id>            - Delete task

Dashboard:
  GET  /api/dashboard              - Get dashboard stats

LOCAL DEVELOPMENT
--------------------------------------------------------------------------------
1. Clone repository: git clone https://github.com/Rohini-Koli9/team-task-manager.git
2. Install dependencies: pip install -r requirements.txt
3. Set environment variables in .env file
4. Run locally: python app.py
5. Access at: http://localhost:5000

DEMO VIDEO GUIDE (2-5 minutes)
--------------------------------------------------------------------------------
Suggested flow for your demo video:
1. Introduction (0:00-0:30) - Show the live app URL
2. Authentication (0:30-1:00) - Register and login
3. Project Management (1:00-2:00) - Create project, add members
4. Task Management (2:00-3:00) - Create tasks, assign, update status
5. Dashboard (3:00-3:30) - Show statistics and overdue tasks
6. Logout/Conclusion (3:30-4:00) - Summary

SUBMISSION CHECKLIST
--------------------------------------------------------------------------------
☐ Live URL: https://team-task-manager-ethara-ai.up.railway.app
☐ GitHub Repository: https://github.com/Rohini-Koli9/team-task-manager.git
☐ README.txt (this file)
☐ Demo Video (2-5 minutes)

CONTACT
--------------------------------------------------------------------------------
Candidate Name: Rohini Koli
Role Applied: Software Engineer - AI/ML

================================================================================
                              END OF README
================================================================================
