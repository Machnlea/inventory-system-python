from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import os

# 导入日志系统和中间件
# from app.core.logging import setup_logging
# from app.core.middleware import (
#     LoggingMiddleware, 
#     SecurityHeadersMiddleware, 
#     RateLimitMiddleware,
#     ErrorHandlingMiddleware
# )
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.equipment import router as equipment_router
from app.api.departments import router as departments_router
from app.api.dashboard import router as dashboard_router
from app.api.audit_logs import router as audit_logs_router
from app.api.categories import router as categories_router
from app.api.import_export import router as import_export_router
from app.api.attachments import router as attachments_router
from app.api.settings import router as settings_router
from app.api.reports import router as reports_router
from app.api.department_users import router as department_users_router
from app.api.external_api import router as external_api_router
from app.api.calibration import router as calibration_router
from app.api.logs import router as logs_router
from app.api.system import router as system_router
from app.db.database import engine
from app.models import models

# 初始化日志系统
from app.core.logging import setup_logging
log_manager = setup_logging()

# 获取应用日志记录器
app_logger = logging.getLogger("app")
app_logger.info("正在启动设备台账管理系统...")

# 创建数据库表
models.Base.metadata.create_all(bind=engine)
app_logger.info("数据库表创建完成")

app = FastAPI(
    title="设备台账管理系统",
    version="1.0.0",
    description="一个完整的设备台账管理系统，支持设备管理、用户权限控制、部门管理、设备类别管理等功能",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 添加中间件（注意顺序很重要）
from app.core.middleware import LoggingMiddleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # 生产环境应该限制具体域名

app_logger.info("中间件配置完成")

# 静态文件和模板
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")
templates = Jinja2Templates(directory="app/templates")

# 路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(users_router, prefix="/api/users", tags=["用户管理"])
app.include_router(categories_router, prefix="/api/categories", tags=["设备类别管理"])
app.include_router(equipment_router, prefix="/api/equipment", tags=["设备管理"])
app.include_router(departments_router, prefix="/api/departments", tags=["部门管理"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(audit_logs_router, prefix="/api/audit", tags=["操作日志"])
app.include_router(import_export_router, prefix="/api/import", tags=["数据导入导出"])
app.include_router(attachments_router, prefix="/api/attachments", tags=["附件管理"])
app.include_router(settings_router, prefix="/api/settings", tags=["系统设置"])
app.include_router(reports_router, prefix="/api/reports", tags=["统计报表"])
app.include_router(department_users_router, prefix="/api/department", tags=["部门用户"])
app.include_router(external_api_router, prefix="/api/external", tags=["外部系统API"])
app.include_router(calibration_router, prefix="/api", tags=["检定管理"])
app.include_router(logs_router, prefix="/api/logs", tags=["日志管理"])
app.include_router(system_router, prefix="/api/system", tags=["系统管理"])

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
    return templates.TemplateResponse("equipment_view.html", {"request": request, "equipment_id": request.query_params.get("id")})

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
    return templates.TemplateResponse("enhanced_audit.html", {"request": request})

@app.get("/audit/legacy", response_class=HTMLResponse)
async def audit_legacy(request: Request):
    return templates.TemplateResponse("audit.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    # 对于页面访问，我们使用前端JavaScript进行权限控制
    # 后端只负责API的权限验证
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})

@app.get("/logs", response_class=HTMLResponse)
async def logs(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})


# 部门用户页面路由
@app.get("/department/login", response_class=HTMLResponse)
async def department_login(request: Request):
    return templates.TemplateResponse("department_login.html", {"request": request})

@app.get("/department/dashboard", response_class=HTMLResponse)
async def department_dashboard(request: Request):
    return templates.TemplateResponse("department_dashboard.html", {"request": request})

# 管理员密码重置页面
@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/api", response_class=RedirectResponse)
async def api_docs():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    
    app_logger.info("启动Web服务器...")
    app_logger.info("访问地址: http://0.0.0.0:8000")
    app_logger.info("API文档: http://0.0.0.0:8000/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None,  # 禁用uvicorn的默认日志配置，使用我们的日志系统
        access_log=False  # 禁用访问日志，我们用中间件记录
    )
