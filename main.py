from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api import users, auth, equipment, departments, dashboard, audit_logs, categories, import_export, attachments, settings
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
app.include_router(attachments.router, prefix="/api/attachments", tags=["附件管理"])
app.include_router(settings.router, prefix="/api", tags=["系统设置"])

@app.get("/favicon.ico")
async def favicon():
    from fastapi.responses import FileResponse
    return FileResponse("app/static/images/favicon.svg", media_type="image/svg+xml")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/equipment", response_class=HTMLResponse)
async def equipment(request: Request):
    return templates.TemplateResponse("equipment_management.html", {"request": request})

@app.get("/equipment/edit", response_class=HTMLResponse)
async def equipment_edit(request: Request):
    return templates.TemplateResponse("equipment_edit.html", {"request": request})

@app.get("/equipment/view", response_class=HTMLResponse)
async def equipment_view(request: Request):
    return templates.TemplateResponse("equipment_view.html", {"request": request})

@app.get("/categories", response_class=HTMLResponse)
async def categories(request: Request):
    return templates.TemplateResponse("categories.html", {"request": request})

@app.get("/departments", response_class=HTMLResponse)
async def departments(request: Request):
    return templates.TemplateResponse("departments.html", {"request": request})

@app.get("/users", response_class=HTMLResponse)
async def users(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

@app.get("/audit", response_class=HTMLResponse)
async def audit(request: Request):
    return templates.TemplateResponse("audit.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/simple_login_test", response_class=HTMLResponse)
async def simple_login_test(request: Request):
    return templates.TemplateResponse("simple_login_test.html", {"request": request})

@app.get("/test_settings", response_class=HTMLResponse)
async def test_settings(request: Request):
    return templates.TemplateResponse("test_settings.html", {"request": request})

@app.get("/api", response_class=RedirectResponse)
async def api_docs():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
