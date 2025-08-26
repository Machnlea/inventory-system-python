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
                "description": "温湿度计、玻璃液体温度计、温湿度表、标准水银温度计",
                "predefined_names": [
                    "温湿度计", "玻璃液体温度计", "温湿度表", "标准水银温度计", 
                    "工作用玻璃温度计", "迷你温湿度计", "数显温度计", "标准水槽", 
                    "标准油槽", "双金属温度计"
                ]
            },
            {
                "name": "长度/几何量类", 
                "category_code": "DIM", 
                "description": "钢直尺、外径千分尺、游标卡尺、杠杆千分尺",
                "predefined_names": [
                    "钢直尺", "外径千分尺", "游标卡尺", "杠杆千分尺", "钢卷尺", 
                    "深度千分尺", "刀口尺", "刀口直角尺", "高度游标卡尺", "塞尺", 
                    "数显千分尺", "数显卡尺", "深度游标卡尺", "条式水平仪", "内径百分表", 
                    "磁性位移测量仪", "立式光学计", "百分表", "表面粗糙度比较样块"
                ]
            },
            {
                "name": "质量称量类", 
                "category_code": "MAS", 
                "description": "电子台秤、工业天平、电子天平",
                "predefined_names": [
                    "电子台秤", "工业天平", "电子天平", "电子计数秤", 
                    "防爆电子秤", "数字式电子汽车衡", "砝码"
                ]
            },
            {
                "name": "时间测量类", 
                "category_code": "TIM", 
                "description": "电子秒表",
                "predefined_names": ["电子秒表"]
            },
            {
                "name": "容量测量类", 
                "category_code": "VOL", 
                "description": "分度吸量管、酸式滴定管、碱式滴定管、量杯",
                "predefined_names": [
                    "分度吸量管", "酸式滴定管", "碱式滴定管", "量杯", "量筒", 
                    "单标线吸量管", "酸碱两用聚四氟滴定管", "单标线容量瓶", 
                    "可调移液器", "移液枪"
                ]
            },
            {
                "name": "压力测量类", 
                "category_code": "PRE", 
                "description": "乙炔压力表、氧压力表、氢气压力表、氩气压力表",
                "predefined_names": [
                    "乙炔压力表", "氧压力表", "氢气压力表", "氩气压力表", "氮气压力表", 
                    "氦气压力表", "压力表", "抗震压力表", "耐震压力表", "精密真空表", 
                    "精密压力表", "数字式差压计"
                ]
            },
            {
                "name": "电学测试类", 
                "category_code": "ELE", 
                "description": "耐压测试仪、绝缘电阻表、数字多用表、MT500P多路温度记录仪",
                "predefined_names": [
                    "耐压测试仪", "绝缘电阻表", "数字多用表", "MT500P多路温度记录仪", 
                    "高绝缘电阻测试仪", "旋转式直流电阻箱", "转换开关", "表面电阻测试仪"
                ]
            },
            {
                "name": "光学测试类", 
                "category_code": "OPT", 
                "description": "色差仪、白度仪、标准光源对色灯箱、目视比色箱",
                "predefined_names": [
                    "色差仪", "白度仪", "标准光源对色灯箱", "目视比色箱", "黑白格玻璃板", 
                    "铁钴比色计", "光泽度仪", "阿贝折射仪", "反射率测定仪"
                ]
            },
            {
                "name": "环境试验类", 
                "category_code": "CLT", 
                "description": "氙灯老化试验箱、紫外老化试验箱、盐雾试验机",
                "predefined_names": [
                    "氙灯老化试验箱", "紫外老化试验箱", "盐雾试验机", 
                    "高低温交变湿热实验箱", "紫外综合试验箱"
                ]
            },
            {
                "name": "化学分析类", 
                "category_code": "CHE", 
                "description": "气相色谱仪、紫外可见分光光度计、紫外分光光度计",
                "predefined_names": [
                    "气相色谱仪", "紫外可见分光光度计", "紫外分光光度计", 
                    "原子吸收分光光度计", "ICP发射光谱仪", "凝胶色谱仪", 
                    "化学需氧量（COD）快速测定仪", "水分测试仪", 
                    "自动快速平衡法微量闪点测试仪", "笔试PH计", "微量水分测定仪", "PH计"
                ]
            },
            {
                "name": "涂层检测类", 
                "category_code": "COA", 
                "description": "铅笔硬度计、数显卡规式测厚仪、磁性测厚仪、百格板",
                "predefined_names": [
                    "铅笔硬度计", "数显卡规式测厚仪", "磁性测厚仪", "百格板", 
                    "漆膜划格器", "漆膜柔韧性测定仪", "漆膜弹性试验仪", "干燥时间试验器", 
                    "漆膜回粘性测定器", "杯突实验仪", "磨耗仪", "建筑涂料耐洗刷仪", 
                    "流挂仪", "漆膜干燥测定仪", "摩擦系数仪", "涂层测厚仪", 
                    "厚漆腻子稠度测定仪", "比重杯", "摆杆式硬度试验计", "附着力测试仪", 
                    "简支梁冲击试验机", "微机控制电子万能试验机", "颗粒强度测定仪", 
                    "汽车密封条磨耗试验机"
                ]
            },
            {
                "name": "粘度流变类", 
                "category_code": "VIS", 
                "description": "ISO流出杯、涂-1#粘度杯、涂-4#粘度杯、斯托默粘度计",
                "predefined_names": [
                    "ISO流出杯", "涂-1#粘度杯", "涂-4#粘度杯", "斯托默粘度计", 
                    "旋转粘度计", "数字式粘度计", "粘度杯"
                ]
            },
            {
                "name": "流量测量类", 
                "category_code": "FLM", 
                "description": "罗茨流量计、腰轮流量计、齿轮流量计、智能浮子流量计",
                "predefined_names": [
                    "罗茨流量计", "腰轮流量计", "齿轮流量计", "智能浮子流量计"
                ]
            },
            {
                "name": "样品制备类", 
                "category_code": "SAM", 
                "description": "湿膜制备器、涂膜器、漆膜制备器、腻子涂刮器",
                "predefined_names": [
                    "湿膜制备器", "涂膜器", "漆膜制备器", "腻子涂刮器", "可调式制备器（数显式）"
                ]
            },
            {
                "name":"计量标准类",
                "category_code": "STD",
                "description": "计量标准器具、量具、检定设备",
                "predefined_names": [
                    "标准铂电阻温度计", "M1级砝码", 
                ]
            },
            {
                "name": "信号处理与显示类",
                "category_code": "SIG",
                "description": "这些设备都属于工业过程控制中的 “二次仪表” （或称“显示控制仪表”），其特点是接收来自“一次仪表”（如热电偶、热电阻、压力传感器）的信号，进行处理后输出标准信号或进行显示记录。",
                "predefined_names": [
                    "温度变送器","压力变送器", "压力液位变送器", "智能变送器", "数显表","无纸记录仪"
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