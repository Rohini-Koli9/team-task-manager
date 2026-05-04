# Team Task Manager

A full-stack web application for managing team projects and tasks with role-based access control.

**Live URL:** team-task-manager-ethara-ai.up.railway.app

## Features

- **Authentication:** JWT-based signup/login system
- **Project Management:** Create projects, add team members with admin/member roles
- **Task Management:** Create, assign, track tasks with status and priority
- **Dashboard:** Overview of projects, tasks, and overdue items
- **Role-Based Access:** Admin can manage projects/members, members can update tasks

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-JWT-Extended
- **Database:** SQLite (easy deployment)
- **Frontend:** Vanilla JavaScript, HTML/CSS (no build step required)
- **Deployment:** Railway (via Gunicorn)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List my projects
- `POST /api/projects` - Create project
- `GET /api/projects/<id>` - Get project details
- `PUT /api/projects/<id>` - Update project (admin only)
- `DELETE /api/projects/<id>` - Delete project (admin only)

### Project Members
- `POST /api/projects/<id>/members` - Add member (admin only)
- `DELETE /api/projects/<id>/members/<member_id>` - Remove member (admin only)

### Tasks
- `GET /api/projects/<id>/tasks` - List project tasks
- `POST /api/projects/<id>/tasks` - Create task
- `GET /api/tasks/<id>` - Get task details
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task

### Dashboard
- `GET /api/dashboard` - Get dashboard stats and recent tasks

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open http://localhost:5000 in your browser

## Deployment to Railway

1. Push code to GitHub
2. Connect Railway to your GitHub repo
3. Add environment variables in Railway dashboard:
   - `JWT_SECRET_KEY` - Generate a secure random string
   - `DATABASE_URL` - Railway PostgreSQL URL (optional, SQLite is default)
4. Deploy!

## Demo Video

[Link to your demo video]

## Author

Built for Ethara AI Software Engineer Assessment
