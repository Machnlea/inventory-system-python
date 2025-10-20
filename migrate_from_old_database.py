#!/usr/bin/env python3
"""
数据库迁移脚本：从老版本的 inventory.db 迁移到当前系统数据库
支持设备台账管理系统的数据升级

作者：Claude AI Assistant
创建时间：2025-10-20
"""

import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.models import models


class DatabaseMigrator:
    """数据库迁移器"""

    def __init__(self, old_db_path: str = "old_inventory.db"):
        self.old_db_path = old_db_path
        self.new_db = SessionLocal()
        self.old_conn = None
        self.migration_stats = {
            'departments': {'old': 0, 'new': 0, 'errors': 0},
            'equipment_categories': {'old': 0, 'new': 0, 'errors': 0},
            'users': {'old': 0, 'new': 0, 'errors': 0},
            'equipments': {'old': 0, 'new': 0, 'errors': 0},
            'calibration_history': {'old': 0, 'new': 0, 'errors': 0},
            'audit_logs': {'old': 0, 'new': 0, 'errors': 0},
            'user_categories': {'old': 0, 'new': 0, 'errors': 0},
            'user_equipment_permissions': {'old': 0, 'new': 0, 'errors': 0}
        }

    def connect_old_database(self) -> bool:
        """连接老数据库"""
        try:
            if not os.path.exists(self.old_db_path):
                print(f"❌ 错误：老数据库文件 {self.old_db_path} 不存在")
                return False

            self.old_conn = sqlite3.connect(self.old_db_path)
            self.old_conn.row_factory = sqlite3.Row
            print(f"✅ 成功连接老数据库：{self.old_db_path}")
            return True
        except Exception as e:
            print(f"❌ 连接老数据库失败：{e}")
            return False

    def backup_current_database(self) -> bool:
        """备份当前数据库"""
        try:
            backup_path = f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

            # 获取当前数据库路径
            current_db_url = str(engine.url).replace('sqlite:///', '')
            if os.path.exists(current_db_url):
                import shutil
                shutil.copy2(current_db_url, backup_path)
                print(f"✅ 当前数据库已备份至：{backup_path}")
            else:
                print("⚠️  当前数据库文件不存在，跳过备份")
            return True
        except Exception as e:
            print(f"⚠️  数据库备份失败：{e}")
            return False

    def get_table_count(self, table_name: str, connection) -> int:
        """获取表记录数"""
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        except:
            return 0

    def migrate_departments(self) -> bool:
        """迁移部门数据"""
        print("\n🔄 开始迁移部门数据...")
        try:
            cursor = self.old_conn.cursor()
            cursor.execute("SELECT * FROM departments")
            old_departments = cursor.fetchall()

            self.migration_stats['departments']['old'] = len(old_departments)

            for dept in old_departments:
                try:
                    # 检查是否已存在
                    existing = self.new_db.query(models.Department).filter(
                        models.Department.name == dept['name']
                    ).first()

                    if existing:
                        print(f"  ⚠️  部门 '{dept['name']}' 已存在，跳过")
                        continue

                    # 创建新部门记录
                    new_dept = models.Department(
                        name=dept['name'],
                        code=dept['code'],
                        description=dept['description'] if dept['description'] else None
                    )

                    self.new_db.add(new_dept)
                    self.migration_stats['departments']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移部门 '{dept.get('name', 'Unknown')}' 失败：{e}")
                    self.migration_stats['departments']['errors'] += 1

            self.new_db.commit()
            print(f"✅ 部门迁移完成：新增 {self.migration_stats['departments']['new']} 个")
            return True

        except Exception as e:
            print(f"❌ 部门迁移失败：{e}")
            self.new_db.rollback()
            return False

    def migrate_equipment_categories(self) -> bool:
        """迁移设备类别数据"""
        print("\n🔄 开始迁移设备类别数据...")
        try:
            cursor = self.old_conn.cursor()
            cursor.execute("SELECT * FROM equipment_categories")
            old_categories = cursor.fetchall()

            self.migration_stats['equipment_categories']['old'] = len(old_categories)

            for category in old_categories:
                try:
                    # 检查是否已存在
                    existing = self.new_db.query(models.EquipmentCategory).filter(
                        models.EquipmentCategory.name == category['name']
                    ).first()

                    if existing:
                        print(f"  ⚠️  类别 '{category['name']}' 已存在，跳过")
                        continue

                    # 处理预定义名称
                    predefined_names = None
                    if category['predefined_names']:
                        try:
                            predefined_names = json.loads(category['predefined_names'])
                        except:
                            predefined_names = None

                    # 创建新设备类别记录
                    new_category = models.EquipmentCategory(
                        name=category['name'],
                        code=category['code'],
                        description=category['description'] if category['description'] else None,
                        predefined_names=predefined_names
                    )

                    self.new_db.add(new_category)
                    self.migration_stats['equipment_categories']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移类别 '{category.get('name', 'Unknown')}' 失败：{e}")
                    self.migration_stats['equipment_categories']['errors'] += 1

            self.new_db.commit()
            print(f"✅ 设备类别迁移完成：新增 {self.migration_stats['equipment_categories']['new']} 个")
            return True

        except Exception as e:
            print(f"❌ 设备类别迁移失败：{e}")
            self.new_db.rollback()
            return False

    def migrate_users(self) -> bool:
        """迁移用户数据"""
        print("\n🔄 开始迁移用户数据...")
        try:
            cursor = self.old_conn.cursor()
            cursor.execute("SELECT * FROM users")
            old_users = cursor.fetchall()

            self.migration_stats['users']['old'] = len(old_users)

            for user in old_users:
                try:
                    # 检查是否已存在
                    existing = self.new_db.query(models.User).filter(
                        models.User.username == user['username']
                    ).first()

                    if existing:
                        print(f"  ⚠️  用户 '{user['username']}' 已存在，跳过")
                        continue

                    # 创建新用户记录
                    new_user = models.User(
                        username=user['username'],
                        hashed_password=user['hashed_password'],
                        is_admin=bool(user['is_admin']),
                        user_type=user['user_type'] if user['user_type'] else 'local',
                        department_id=user['department_id'] if user['department_id'] else None,
                        is_active=bool(user['is_active']) if user['is_active'] is not None else True,
                        last_login=user['last_login'] if user['last_login'] else None,
                        password_reset_at=user['password_reset_at'] if user['password_reset_at'] else None,
                        security_question=user['security_question'] if user['security_question'] else None,
                        security_answer_hash=user['security_answer_hash'] if user['security_answer_hash'] else None
                    )

                    self.new_db.add(new_user)
                    self.migration_stats['users']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移用户 '{user.get('username', 'Unknown')}' 失败：{e}")
                    self.migration_stats['users']['errors'] += 1

            self.new_db.commit()
            print(f"✅ 用户迁移完成：新增 {self.migration_stats['users']['new']} 个")
            return True

        except Exception as e:
            print(f"❌ 用户迁移失败：{e}")
            self.new_db.rollback()
            return False

    def migrate_user_categories_and_permissions(self) -> bool:
        """迁移用户类别和权限数据"""
        print("\n🔄 开始迁移用户权限数据...")
        try:
            # 迁移用户类别
            cursor = self.old_conn.cursor()
            cursor.execute("SELECT * FROM user_categories")
            old_user_categories = cursor.fetchall()

            self.migration_stats['user_categories']['old'] = len(old_user_categories)

            for uc in old_user_categories:
                try:
                    # 检查是否已存在
                    existing = self.new_db.query(models.UserCategory).filter(
                        models.UserCategory.user_id == uc['user_id'],
                        models.UserCategory.category_id == uc['category_id']
                    ).first()

                    if existing:
                        continue

                    # 创建新用户类别记录
                    new_uc = models.UserCategory(
                        user_id=uc['user_id'],
                        category_id=uc['category_id']
                    )

                    self.new_db.add(new_uc)
                    self.migration_stats['user_categories']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移用户类别关系失败：{e}")
                    self.migration_stats['user_categories']['errors'] += 1

            # 迁移用户设备权限
            cursor.execute("SELECT * FROM user_equipment_permissions")
            old_permissions = cursor.fetchall()

            self.migration_stats['user_equipment_permissions']['old'] = len(old_permissions)

            for perm in old_permissions:
                try:
                    # 检查是否已存在
                    existing = self.new_db.query(models.UserEquipmentPermission).filter(
                        models.UserEquipmentPermission.user_id == perm['user_id'],
                        models.UserEquipmentPermission.category_id == perm['category_id'],
                        models.UserEquipmentPermission.equipment_name == perm['equipment_name']
                    ).first()

                    if existing:
                        continue

                    # 创建新用户设备权限记录
                    new_perm = models.UserEquipmentPermission(
                        user_id=perm['user_id'],
                        category_id=perm['category_id'],
                        equipment_name=perm['equipment_name']
                    )

                    self.new_db.add(new_perm)
                    self.migration_stats['user_equipment_permissions']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移用户设备权限失败：{e}")
                    self.migration_stats['user_equipment_permissions']['errors'] += 1

            self.new_db.commit()
            print(f"✅ 用户权限迁移完成：用户类别 {self.migration_stats['user_categories']['new']} 个，设备权限 {self.migration_stats['user_equipment_permissions']['new']} 个")
            return True

        except Exception as e:
            print(f"❌ 用户权限迁移失败：{e}")
            self.new_db.rollback()
            return False

    def migrate_equipments(self) -> bool:
        """迁移设备数据"""
        print("\n🔄 开始迁移设备数据...")
        try:
            cursor = self.old_conn.cursor()
            cursor.execute("SELECT * FROM equipments")
            old_equipments = cursor.fetchall()

            self.migration_stats['equipments']['old'] = len(old_equipments)

            for eq in old_equipments:
                try:
                    # 检查是否已存在（根据内部编号）
                    existing = self.new_db.query(models.Equipment).filter(
                        models.Equipment.internal_id == eq['internal_id']
                    ).first()

                    if existing:
                        print(f"  ⚠️  设备 '{eq['name']}' ({eq['internal_id']}) 已存在，跳过")
                        continue

                    # 创建新设备记录
                    new_eq = models.Equipment(
                        department_id=eq['department_id'],
                        category_id=eq['category_id'],
                        name=eq['name'],
                        model=eq['model'] if eq['model'] else None,
                        accuracy_level=eq['accuracy_level'] if eq['accuracy_level'] else None,
                        measurement_range=eq['measurement_range'],
                        calibration_cycle=eq['calibration_cycle'] if eq['calibration_cycle'] else None,
                        calibration_date=eq['calibration_date'] if eq['calibration_date'] else None,
                        valid_until=eq['valid_until'] if eq['valid_until'] else None,
                        calibration_method=eq['calibration_method'] if eq['calibration_method'] else None,
                        certificate_number=eq['certificate_number'] if eq['certificate_number'] else None,
                        verification_agency=eq['verification_agency'] if eq['verification_agency'] else None,
                        certificate_form=eq['certificate_form'] if eq['certificate_form'] else None,
                        internal_id=eq['internal_id'] if eq['internal_id'] else None,
                        manufacturer_id=eq['manufacturer_id'] if eq['manufacturer_id'] else None,
                        installation_location=eq['installation_location'] if eq['installation_location'] else None,
                        manufacturer=eq['manufacturer'] if eq['manufacturer'] else None,
                        manufacture_date=eq['manufacture_date'] if eq['manufacture_date'] else None,
                        scale_value=eq['scale_value'] if eq['scale_value'] else None,
                        management_level=eq['management_level'] if eq['management_level'] else None,
                        original_value=eq['original_value'] if eq['original_value'] else None,
                        status=eq['status'] if eq['status'] else '在用',
                        status_change_date=eq['status_change_date'] if eq['status_change_date'] else None,
                        notes=eq['notes'] if eq['notes'] else None,
                        calibration_notes=eq['calibration_notes'] if eq['calibration_notes'] else None,
                        disposal_reason=eq['disposal_reason'] if eq['disposal_reason'] else None,
                        current_calibration_result=eq['current_calibration_result'] if eq['current_calibration_result'] else None,
                        created_at=eq['created_at'] if eq['created_at'] else datetime.now(),
                        updated_at=eq['updated_at'] if eq['updated_at'] else None
                    )

                    self.new_db.add(new_eq)
                    self.migration_stats['equipments']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移设备 '{eq.get('name', 'Unknown')}' 失败：{e}")
                    self.migration_stats['equipments']['errors'] += 1

            self.new_db.commit()
            print(f"✅ 设备迁移完成：新增 {self.migration_stats['equipments']['new']} 个")
            return True

        except Exception as e:
            print(f"❌ 设备迁移失败：{e}")
            self.new_db.rollback()
            return False

    def migrate_calibration_history(self) -> bool:
        """迁移检定历史数据"""
        print("\n🔄 开始迁移检定历史数据...")
        try:
            cursor = self.old_conn.cursor()
            cursor.execute("SELECT * FROM calibration_history")
            old_history = cursor.fetchall()

            self.migration_stats['calibration_history']['old'] = len(old_history)

            for history in old_history:
                try:
                    # 创建新检定历史记录
                    new_history = models.CalibrationHistory(
                        equipment_id=history['equipment_id'],
                        calibration_date=history['calibration_date'] if history['calibration_date'] else None,
                        valid_until=history['valid_until'] if history['valid_until'] else None,
                        calibration_method=history['calibration_method'] if history['calibration_method'] else None,
                        calibration_result=history['calibration_result'] if history['calibration_result'] else None,
                        certificate_number=history['certificate_number'] if history['certificate_number'] else None,
                        certificate_form=history['certificate_form'] if history['certificate_form'] else None,
                        verification_agency=history['verification_agency'] if history['verification_agency'] else None,
                        notes=history['notes'] if history['notes'] else None,
                        created_at=history['created_at'] if history['created_at'] else datetime.now(),
                        created_by=history['created_by'] if history['created_by'] else None,
                        is_rolled_back=bool(history['is_rolled_back']) if history['is_rolled_back'] is not None else False,
                        rolled_back_at=history['rolled_back_at'] if history['rolled_back_at'] else None,
                        rolled_back_by=history['rolled_back_by'] if history['rolled_back_by'] else None,
                        rollback_reason=history['rollback_reason'] if history['rollback_reason'] else None
                    )

                    self.new_db.add(new_history)
                    self.migration_stats['calibration_history']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移检定历史记录失败：{e}")
                    self.migration_stats['calibration_history']['errors'] += 1

            self.new_db.commit()
            print(f"✅ 检定历史迁移完成：新增 {self.migration_stats['calibration_history']['new']} 条")
            return True

        except Exception as e:
            print(f"❌ 检定历史迁移失败：{e}")
            self.new_db.rollback()
            return False

    def migrate_audit_logs(self) -> bool:
        """迁移审计日志数据"""
        print("\n🔄 开始迁移审计日志数据...")
        try:
            cursor = self.old_conn.cursor()
            cursor.execute("SELECT * FROM audit_logs")
            old_logs = cursor.fetchall()

            self.migration_stats['audit_logs']['old'] = len(old_logs)

            for log in old_logs:
                try:
                    # 创建新审计日志记录
                    new_log = models.AuditLog(
                        user_id=log['user_id'] if log['user_id'] else None,
                        equipment_id=log['equipment_id'] if log['equipment_id'] else None,
                        action=log['action'] if log['action'] else None,
                        description=log['description'] if log['description'] else None,
                        old_value=log['old_value'] if log['old_value'] else None,
                        new_value=log['new_value'] if log['new_value'] else None,
                        created_at=log['created_at'] if log['created_at'] else datetime.now(),
                        operation_type='equipment',  # 默认操作类型
                        target_table='equipments',  # 默认目标表
                        target_id=log['equipment_id'] if log['equipment_id'] else None,
                        parent_log_id=None,  # 老版本没有这个字段
                        rollback_log_id=None,  # 老版本没有这个字段
                        is_rollback=bool(log['is_rollback_operation']) if log['is_rollback_operation'] is not None else False,
                        rollback_reason=None  # 老版本没有这个字段
                    )

                    self.new_db.add(new_log)
                    self.migration_stats['audit_logs']['new'] += 1

                except Exception as e:
                    print(f"  ❌ 迁移审计日志失败：{e}")
                    self.migration_stats['audit_logs']['errors'] += 1

            self.new_db.commit()
            print(f"✅ 审计日志迁移完成：新增 {self.migration_stats['audit_logs']['new']} 条")
            return True

        except Exception as e:
            print(f"❌ 审计日志迁移失败：{e}")
            self.new_db.rollback()
            return False

    def print_migration_summary(self):
        """打印迁移汇总信息"""
        print("\n" + "="*60)
        print("📊 数据迁移汇总报告")
        print("="*60)

        total_old = 0
        total_new = 0
        total_errors = 0

        for table, stats in self.migration_stats.items():
            if stats['old'] > 0:
                old = stats['old']
                new = stats['new']
                errors = stats['errors']

                total_old += old
                total_new += new
                total_errors += errors

                status = "✅" if errors == 0 else "⚠️" if new > 0 else "❌"
                print(f"{status} {table:<25}: {old:>4} → {new:>4} (错误: {errors:>2})")

        print("-"*60)
        print(f"📈 总计: {total_old} 条记录 → {total_new} 条记录 (总错误: {total_errors})")

        if total_errors == 0:
            print("🎉 数据迁移完全成功！")
        elif total_new > 0:
            print("✅ 数据迁移基本完成，部分记录迁移失败")
        else:
            print("❌ 数据迁移失败")

    def run_migration(self) -> bool:
        """执行完整迁移流程"""
        print("🚀 开始数据库迁移流程...")
        print("="*60)

        # 连接老数据库
        if not self.connect_old_database():
            return False

        # 备份当前数据库
        if not self.backup_current_database():
            print("⚠️  数据库备份失败，但继续迁移...")

        # 显示迁移前信息
        print("\n📋 迁移前信息:")
        print(f"老数据库路径: {self.old_db_path}")
        print(f"新数据库路径: {str(engine.url).replace('sqlite:///', '')}")

        # 执行迁移（按依赖关系顺序）
        migration_steps = [
            self.migrate_departments,
            self.migrate_equipment_categories,
            self.migrate_users,
            self.migrate_user_categories_and_permissions,
            self.migrate_equipments,
            self.migrate_calibration_history,
            self.migrate_audit_logs
        ]

        success_count = 0
        for step in migration_steps:
            try:
                if step():
                    success_count += 1
                else:
                    print(f"❌ 迁移步骤失败，停止后续迁移")
                    break
            except Exception as e:
                print(f"❌ 迁移步骤出现异常：{e}")
                break

        # 关闭连接
        if self.old_conn:
            self.old_conn.close()
        self.new_db.close()

        # 打印汇总报告
        self.print_migration_summary()

        return success_count == len(migration_steps)


def main():
    """主函数"""
    print("📦 设备台账管理系统 - 数据库迁移工具")
    print("="*60)
    print("⚠️  警告：此操作将修改当前数据库，请确保已备份重要数据")
    print("="*60)

    # 确认执行
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("🤖 自动模式，开始迁移...")
    else:
        confirm = input("是否继续执行数据迁移？(y/N): ").lower().strip()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 用户取消迁移")
            return

    # 检查老数据库文件
    old_db_path = "old_inventory.db"
    if not os.path.exists(old_db_path):
        print(f"❌ 错误：老数据库文件 '{old_db_path}' 不存在")
        print("请将老数据库文件放置在项目根目录并命名为 'old_inventory.db'")
        return

    # 创建迁移器并执行迁移
    migrator = DatabaseMigrator(old_db_path)
    success = migrator.run_migration()

    if success:
        print("\n🎉 数据迁移成功完成！")
        print("💡 建议：")
        print("  1. 重启应用程序以加载新数据")
        print("  2. 验证迁移后的数据完整性")
        print("  3. 如有问题，可从备份文件恢复")
    else:
        print("\n❌ 数据迁移失败")
        print("💡 建议：")
        print("  1. 检查错误信息并修复问题")
        print("  2. 从备份文件恢复数据库")
        print("  3. 重新运行迁移脚本")


if __name__ == "__main__":
    main()