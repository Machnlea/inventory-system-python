from app.db.database import SessionLocal, engine
from app.models import models
from app.crud import users, departments, categories
from app.schemas.schemas import UserCreate, DepartmentCreate, EquipmentCategoryCreate
from app.core.config import settings

def init_db():
    # 创建数据库表
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 创建默认管理员用户
        admin_user = users.get_user_by_username(db, settings.ADMIN_USERNAME)
        if not admin_user:
            admin_user_data = UserCreate(
                username=settings.ADMIN_USERNAME,
                password=settings.ADMIN_PASSWORD,
                is_admin=True
            )
            users.create_user(db, admin_user_data)
            print(f"创建默认管理员用户: {settings.ADMIN_USERNAME}")
        
        # 创建默认部门 (包含代码)
        default_departments = [
            {"name": "防腐漆车间", "code": "FF", "description": "防腐产品生产车间"},
            {"name": "工业漆车间", "code": "GY", "description": "工业漆生产车间"},
            {"name": "技术中心", "code": "JS", "description": "技术研发部门"},
            {"name": "水性漆车间", "code": "SX", "description": "水性漆生产车间"},
            {"name": "汽摩漆车间", "code": "QM", "description": "汽摩产品生产车间"},
            {"name": "树脂车间", "code": "SZ", "description": "树脂生产车间"},
            {"name": "通用漆车间", "code": "TY", "description": "通用漆生产车间"},
            {"name": "质管部", "code": "ZG", "description": "质量管理部门"},
            {"name": "服务中心", "code": "FW", "description": "服务支持部门"},
            {"name": "制听车间", "code": "ZT", "description": "制听产品生产车间"},
            {"name": "安环部", "code": "AH", "description": "安全环保部门"},
            {"name": "物管部", "code": "WG", "description": "物资管理部门"},
            {"name": "机修车间", "code": "JX", "description": "机修车间"},
            {"name": "电控部", "code": "DK", "description": "电控部门"},
            {"name": "中试车间", "code": "ZX", "description": "中试车间、防腐中试车间"},
            {"name": "项目办", "code": "XM", "description": "项目办"}
        ]   
        
        for dept_data in default_departments:
            existing_dept = departments.get_department_by_name(db, dept_data["name"])
            if not existing_dept:
                dept_create = DepartmentCreate(**dept_data)
                departments.create_department(db, dept_create)
                print(f"创建部门: {dept_data['name']}")
        
        # 创建默认设备类别 (使用三字母代码，包含预定义名称)
        default_categories = [
            {
                "name": "温度环境类", 
                "category_code": "TEM", 
                "description": "Temperature and Environment 用于测量和监控温度、湿度等环境参数的设备，包括各类温度计、温湿度计。",
                "predefined_names": [
                    "玻璃液体温度计",
                    "铂热电阻",
                    "数字式温湿度计",
                    "双金属温度计",
                    "温湿度表",
                ]
            },
            {
                "name": "长度/几何量类", 
                "category_code": "DIM", 
                "description": "Dimension Measurement用于测量物体几何尺寸、形状、位置的精密的长度测量工具和量仪。",
                "predefined_names": [
                   "百分表",
                    "表面粗糙度比较样块",
                    "磁性位移测量仪",
                    "刀口尺",
                    "钢卷尺",
                    "钢直尺",
                    "立式光学计",
                    "内径百分表",
                    "千分尺",
                    "塞尺",
                    "条式水平仪",
                    "游标卡尺",
                ]
            },
            {
                "name": "质量称量类", 
                "category_code": "MAS", 
                "description": "Mass Weighing 用于测量物体质量的称重设备和相关配件。",
                "predefined_names": [ 
                    "案秤",
                    "地上衡",
                    "电子秤",
                    "电子天平",
                    "数字指示秤",
                    "台秤",
                ]
            },
            {
                "name": "时间测量类", 
                "category_code": "TIM", 
                "description": "Time Measurement 用于测量时间间隔的仪表。",
                "predefined_names": [
                    "电子秒表",
                    "机械秒表"
                    ]
            },
            {
                "name": "容量测量类", 
                "category_code": "VOL", 
                "description": "Volume Measurement, 用于精密量取、测量或容纳液体体积的玻璃器皿和装置。",
                "predefined_names": [
                    "单标线容量瓶",
                    "滴定管",
                    "可调移液器",
                    "量杯",
                    "量筒",
                    "吸量管",
                    "移液枪",
                ]
            },
            {
                "name": "压力测量类", 
                "category_code": "PRE", 
                "description": "Pressure Measurement, 用于测量流体压力、真空度或压力差的仪表。",
                "predefined_names": [
                    "压力表",
                    "电接点压力表",
                ]
            },
            {
                "name": "电学测试类", 
                "category_code": "ELE", 
                "description": "Electrical Testing, 用于测量电压、电流、电阻等电学参数的仪表。",
                "predefined_names": [
                    "MT500P多路温度记录仪",
                    "表面电阻测试仪",
                    "高绝缘电阻测试仪",
                    "绝缘电阻表",
                ]
            },
            {
                "name": "光学测试类", 
                "category_code": "OPT", 
                "description": "Optical Testing, 用于测量材料光学性能（如颜色、光泽、折射率、白度）的仪器和设备。",
                "predefined_names": [
                    "阿贝折射仪",
                    "白度仪",
                    "标准光源对色灯箱",
                    "反射率测定仪",
                    "光泽度仪",
                    "黑白格玻璃板",
                    "目视比色箱",
                    "色差仪",
                    "铁钴比色计",
                ]
            },
            {
                "name": "环境试验类", 
                "category_code": "CLT", 
                "description": "Climatic Testing, 用于模拟极端环境条件（如温度、湿度、光照、腐蚀）以测试产品耐久性和可靠性的设备。",
                "predefined_names": [
                    "高低温交变湿热实验箱",
                    "恒温恒湿机",
                    "热球式风速仪",
                    "氙灯老化试验箱",
                    "盐雾试验机",
                    "紫外试验箱",
                ]
            },
            {
                "name": "化学分析类", 
                "category_code": "CHE", 
                "description": "Chemical Analysis, 用于物质的定性分析、定量分析及物理化学参数测定的精密分析仪器。",
                "predefined_names": [
                    "ICP发射光谱仪"
                    "PH计",
                    "多种气体检测仪",
                    "化学需氧量（COD）快速测定仪",
                    "气相色谱仪",
                    "水分测试仪",
                    "原子吸收分光光度计",
                    "紫外可见分光光度计",
                    "自动快速平衡法微量闪点测试仪",
                ]
            },
            {
                "name": "涂层检测类", 
                "category_code": "COA", 
                "description": "Coating Testing, 专用于测试涂料、油墨、涂层等各种性能（如物理机械性能、光学性能、防护性能）的仪器和设备。",
                "predefined_names": [
                    "百格板",
                    "摆杆式硬度试验计",
                    "杯突实验仪",
                    "比重杯",
                    "测厚仪",
                    "冲击试验器",
                    "附着力试验仪",
                    "干燥时间试验器",
                    "刮板细度计",
                    "厚漆腻子稠度测定仪",
                    "简支梁冲击试验机",
                    "建筑涂料耐洗刷仪",
                    "颗粒强度测定仪",
                    "流挂仪",
                    "摩擦系数仪",
                    "磨耗仪",
                    "漆膜弹性试验仪",
                    "漆膜划格器",
                    "漆膜回粘性测定器",
                    "漆膜柔韧性测定仪",
                    "铅笔硬度计",
                    "微机控制电子万能试验机",
                ]
            },
            {
                "name": "粘度流变类", 
                "category_code": "VIS", 
                "description": "Viscosity Measurement, 用于测量流体粘度及其流动特性的仪器。",
                "predefined_names": [
                    "ISO流出杯",
                    "斯托默粘度计",
                    "涂-1#粘度杯",
                    "涂-4#粘度杯",
                    "旋转粘度计",
                ]
            },
            {
                "name": "流量测量类", 
                "category_code": "FLM", 
                "description": "Flow Measurement, 用于测量管道中流体（液体、气体）流动速率（流量）的仪表。",
                "predefined_names": [
                   "齿轮流量计",
                    "罗茨流量计",
                    "涡轮流量计",
                    "腰轮流量计",
                    "智能浮子流量计",
                ]
            },
            {
                "name": "样品制备类", 
                "category_code": "SAM", 
                "description": "Sample Preparation, 用于制备标准化、一致性测试样板的专用工具。",
                "predefined_names": [
                    "腻子涂刮器",
                    "涂膜器",
                    "涂膜制备器",
                ]
            },
            {
                "name":"计量标准类",
                "category_code": "STD",
                "description": "Standard Equipment, 作为公司最高计量标准，用于量值传递、检定或校准其他工作计量器具的基准设备、标准器及配套设备。",
                "predefined_names": [
                    "标准铂电阻温度计",
                    "标准水槽",
                    "标准水银温度计",
                    "标准油槽",
                    "电子秒表",
                    "电子天平",
                    "砝码",
                    "工作用玻璃温度计",
                    "精密压力表",
                    "精密真空表",
                    "绝缘电阻表",
                    "耐压测试仪",
                    "数字多用表",
                    "数字式温湿度计",
                    "直流电阻器",
                    "转换开关",
                ]
            },
            {
                "name": "信号处理与显示类",
                "category_code": "SIG",
                "description": "Signal Processing and Indication, 工业过程控制中的“二次仪表”，其核心功能是接收来自传感器或“一次仪表”的信号，进行处理、转换、显示、记录或传输标准信号。",
                "predefined_names": [
                    "雷达液位计",
                    "数显表",
                    "温度变送器",
                    "压力变送器",
                    "压力液位变送器",
                    "智能变送器",
                ]
            }
        ]
        
        for cat_data in default_categories:
            existing_cat = categories.get_category_by_name(db, cat_data["name"])
            if not existing_cat:
                cat_create = EquipmentCategoryCreate(**cat_data)
                categories.create_category(db, cat_create)
                print(f"创建设备类别: {cat_data['name']}")
        
        print("数据库初始化完成")
        
    finally:
        db.close()

if __name__ == "__main__":
    init_db()