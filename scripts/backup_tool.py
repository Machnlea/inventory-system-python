#!/usr/bin/env python3
"""
设备台账管理系统 - 数据库备份工具
支持自动备份、清理和状态检查功能
"""

import os
import sys
import sqlite3
import shutil
import argparse
import json
from datetime import datetime, timedelta
import logging
from pathlib import Path

class DatabaseBackupTool:
    def __init__(self, db_path=None, backup_path=None):
        # 设置路径
        self.script_dir = Path(__file__).parent
        self.db_path = Path(db_path) if db_path else self.script_dir / "../data/inventory.db"
        self.backup_path = Path(backup_path) if backup_path else self.script_dir / "../dbbak"
        
        # 确保备份目录存在
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.log_file = self.backup_path / "backup.log"
        self.setup_logging()
        
        # 备份保留策略
        self.retention_days = {
            'daily': 7,      # 保留7天日备份
            'weekly': 4,     # 保留4周周备份  
            'monthly': 12    # 保留12个月月备份
        }
        
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def validate_database(self):
        """验证数据库文件是否存在且有效"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
            
        if not self.db_path.is_file():
            raise ValueError(f"数据库路径不是文件: {self.db_path}")
            
        # 尝试连接数据库验证完整性
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            if not tables:
                raise ValueError("数据库为空或已损坏")
                
            self.logger.info(f"数据库验证成功，包含 {len(tables)} 个表")
            return True
            
        except sqlite3.Error as e:
            raise ValueError(f"数据库验证失败: {e}")
            
    def create_backup(self, backup_type='daily'):
        """创建数据库备份"""
        try:
            # 验证数据库
            self.validate_database()
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"inventory_{backup_type}_{timestamp}.db"
            backup_file = self.backup_path / backup_filename
            
            # 创建备份
            self.logger.info(f"开始创建 {backup_type} 备份: {backup_filename}")
            
            # 使用sqlite3备份API
            source_conn = sqlite3.connect(str(self.db_path))
            backup_conn = sqlite3.connect(str(backup_file))
            
            with backup_conn:
                source_conn.backup(backup_conn)
                
            source_conn.close()
            backup_conn.close()
            
            # 验证备份文件
            if not backup_file.exists() or backup_file.stat().st_size == 0:
                raise Exception("备份文件创建失败")
                
            # 创建备份信息文件
            info_file = self.backup_path / f"inventory_{backup_type}_{timestamp}.json"
            backup_info = {
                'timestamp': timestamp,
                'backup_type': backup_type,
                'source_file': str(self.db_path),
                'backup_file': str(backup_file),
                'file_size': backup_file.stat().st_size,
                'created_at': datetime.now().isoformat()
            }
            
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"备份创建成功: {backup_filename} ({backup_file.stat().st_size} bytes)")
            return backup_file
            
        except Exception as e:
            self.logger.error(f"备份创建失败: {e}")
            raise
            
    def clean_old_backups(self):
        """清理旧备份文件"""
        self.logger.info("开始清理旧备份文件")
        
        cleaned_count = 0
        current_date = datetime.now()
        
        # 遍历备份目录
        for backup_file in self.backup_path.glob("inventory_*.db"):
            try:
                # 从文件名提取备份类型和时间
                name_parts = backup_file.stem.split('_')
                if len(name_parts) >= 3:
                    backup_type = name_parts[1]
                    date_str = name_parts[2]
                    
                    # 解析备份时间
                    try:
                        backup_date = datetime.strptime(date_str, "%Y%m%d")
                        days_old = (current_date - backup_date).days
                        
                        # 根据备份类型判断是否需要删除
                        should_delete = False
                        if backup_type == 'daily' and days_old > self.retention_days['daily']:
                            should_delete = True
                        elif backup_type == 'weekly' and days_old > self.retention_days['weekly'] * 7:
                            should_delete = True
                        elif backup_type == 'monthly' and days_old > self.retention_days['monthly'] * 30:
                            should_delete = True
                            
                        if should_delete:
                            # 删除备份文件和对应的信息文件
                            backup_file.unlink()
                            info_file = backup_file.with_suffix('.json')
                            if info_file.exists():
                                info_file.unlink()
                            cleaned_count += 1
                            self.logger.info(f"删除旧备份: {backup_file.name}")
                            
                    except ValueError:
                        # 无法解析日期的文件跳过
                        continue
                        
            except Exception as e:
                self.logger.warning(f"清理备份文件时出错 {backup_file}: {e}")
                continue
                
        self.logger.info(f"清理完成，删除了 {cleaned_count} 个旧备份文件")
        return cleaned_count
        
    def get_backup_status(self):
        """获取备份状态信息"""
        status = {
            'database_exists': self.db_path.exists(),
            'database_size': self.db_path.stat().st_size if self.db_path.exists() else 0,
            'backup_path': str(self.backup_path),
            'backups': [],
            'total_backups': 0,
            'last_backup': None,
            'backup_types': {'daily': 0, 'weekly': 0, 'monthly': 0}
        }
        
        if not self.backup_path.exists():
            return status
            
        # 统计备份文件
        for backup_file in self.backup_path.glob("inventory_*.db"):
            try:
                name_parts = backup_file.stem.split('_')
                if len(name_parts) >= 3:
                    backup_type = name_parts[1]
                    date_str = name_parts[2]
                    
                    backup_info = {
                        'filename': backup_file.name,
                        'type': backup_type,
                        'size': backup_file.stat().st_size,
                        'created': datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat()
                    }
                    
                    status['backups'].append(backup_info)
                    status['total_backups'] += 1
                    
                    if backup_type in status['backup_types']:
                        status['backup_types'][backup_type] += 1
                        
                    # 更新最后备份时间
                    if status['last_backup'] is None or backup_info['created'] > status['last_backup']:
                        status['last_backup'] = backup_info['created']
                        
            except Exception as e:
                self.logger.warning(f"分析备份文件时出错 {backup_file}: {e}")
                continue
                
        # 按创建时间排序
        status['backups'].sort(key=lambda x: x['created'], reverse=True)
        
        return status
        
    def restore_backup(self, backup_file, target_file=None):
        """从备份恢复数据库"""
        backup_file = Path(backup_file)
        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
        target_file = Path(target_file) if target_file else self.db_path
        
        self.logger.info(f"开始恢复备份: {backup_file} -> {target_file}")
        
        # 创建目标目录
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果目标文件存在，先创建备份
        if target_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = target_file.with_name(f"{target_file.stem}_pre_restore_{timestamp}{target_file.suffix}")
            shutil.copy2(target_file, pre_restore_backup)
            self.logger.info(f"原数据库已备份到: {pre_restore_backup}")
            
        # 执行恢复
        try:
            backup_conn = sqlite3.connect(str(backup_file))
            target_conn = sqlite3.connect(str(target_file))
            
            with target_conn:
                backup_conn.backup(target_conn)
                
            backup_conn.close()
            target_conn.close()
            
            self.logger.info(f"恢复完成: {target_file}")
            return target_file
            
        except Exception as e:
            self.logger.error(f"恢复失败: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='数据库备份工具')
    parser.add_argument('--action', choices=['backup', 'clean', 'status', 'restore'], 
                       default='backup', help='执行的操作')
    parser.add_argument('--type', choices=['daily', 'weekly', 'monthly'], 
                       default='daily', help='备份类型')
    parser.add_argument('--db-path', help='数据库文件路径')
    parser.add_argument('--backup-path', help='备份目录路径')
    parser.add_argument('--restore-file', help='恢复时指定的备份文件')
    
    args = parser.parse_args()
    
    try:
        # 初始化备份工具
        tool = DatabaseBackupTool(args.db_path, args.backup_path)
        
        if args.action == 'backup':
            tool.create_backup(args.type)
            print("备份创建成功")
            
        elif args.action == 'clean':
            cleaned = tool.clean_old_backups()
            print(f"清理完成，删除了 {cleaned} 个旧备份文件")
            
        elif args.action == 'status':
            status = tool.get_backup_status()
            print(json.dumps(status, ensure_ascii=False, indent=2))
            
        elif args.action == 'restore':
            if not args.restore_file:
                print("错误: 恢复操作需要指定 --restore-file 参数")
                sys.exit(1)
            tool.restore_backup(args.restore_file)
            print("恢复完成")
            
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()