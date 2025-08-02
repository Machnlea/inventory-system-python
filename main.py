from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api import users, auth, equipment, departments, dashboard, audit_logs, categories, import_export
from app.db.database import engine
from app.models import models

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="设备台账管理系统",
    version="1.0.0",
    description="一个完整的设备台账管理系统，支持设备管理、用户权限控制、部门管理、设备类别管理等功能",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(categories.router, prefix="/api/categories", tags=["设备类别管理"])
app.include_router(equipment.router, prefix="/api/equipment", tags=["设备管理"])
app.include_router(departments.router, prefix="/api/departments", tags=["部门管理"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(audit_logs.router, prefix="/api/audit", tags=["操作日志"])
app.include_router(import_export.router, prefix="/api/import", tags=["数据导入导出"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api", response_class=RedirectResponse)
async def api_docs():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
