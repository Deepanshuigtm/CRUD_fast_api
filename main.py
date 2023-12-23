from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from pydantic import BaseModel
from typing import Optional, List


SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

class TaskCreate(BaseModel):
    title: str
    description: str
    completed: bool

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = False

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

@app.get("/")
def index():
    return RedirectResponse(url='/docs')

@app.post("/tasks/")
def create_task(task: TaskCreate):
    db = SessionLocal()

    new_task = Task(title=task.title, description=task.description, completed=task.completed)

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@app.get("/get-task-by-id/{task_id}")
def get_task_by_id(task_id: int):
    db = SessionLocal()

    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

@app.put("/update-task/{task_id}")
def update_task(task_id: int, taskupdate: TaskUpdate):
    db = SessionLocal()
    
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if taskupdate.title != None:
        task.title = taskupdate.title
    if taskupdate.description != None:
        task.description = taskupdate.description
    if taskupdate.completed != None:
        task.completed = taskupdate.completed

    db.commit()

    return {"message": "Task updated successfully"}

@app.delete("/delete-task/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

@app.get("/tasks/", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            completed=task.completed
        )
        for task in tasks
    ]

@app.get("/get_filtered_tasks/", response_model=List[TaskResponse])
def get_filtered_tasks(completed: Optional[bool] = Query(None), db: Session = Depends(get_db)):
    # Initialize query to get all tasks
    query = db.query(Task)

    # If 'completed' parameter is provided, filter tasks based on completion status
    if completed is not None:
        query = query.filter(Task.completed == completed)

    tasks = query.all()

    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            completed=task.completed
        )
        for task in tasks
    ]