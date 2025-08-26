#!/usr/bin/env python3
"""
设备台账管理系统 - 自动Excel导出工具
支持定时导出设备数据到Excel文件并发送到终端设备
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
import argparse
from typing import Dict, Any, Optional

class AutoExcelExporter:
    def __init__(self, config_file=None):
        self.script_dir = Path(__file__).parent
        self.project_dir = self.script_dir.parent
        
        # 默认配置
        self.config = {
            'api_base_url': 'http://127.0.0.1:8000',
            'export_dir': self.project_dir / 'auto_exports',
            'default_export_type': 'all',
            'notification_enabled': True,
            'retention_days': 30,
            'auth_credentials': {
                'username': 'admin',
                'password': 'admin123'
            }
        }
        
        # 加载配置文件
        if config_file and Path(config_file).exists():
            self.load_config(config_file)
        
        # 创建导出目录
        self.export_dir = Path(self.config['export_dir'])
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.log_file = self.export_dir / 'auto_export.log'
        self.setup_logging()
        
        # 会话管理
        self.session = requests.Session()
        self.access_token = None
        
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
        
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                self.config.update(user_config)
            self.logger.info(f"已加载配置文件: {config_file}")
        except Exception as e:
            self.logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            
    def login(self):
        """登录获取访问令牌"""
        try:
            login_url = f"{self.config['api_base_url']}/api/auth/login/json"
            credentials = self.config['auth_credentials']
            
            response = self.session.post(login_url, json=credentials)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error(f"登录失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"登录时发生错误: {e}")
            return False
            
    def export_equipment_data(self, export_type='all', filters=None):
        """导出设备数据"""
        if not self.access_token:
            if not self.login():
                raise Exception("无法获取访问令牌")
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if export_type == 'all':
                filename = f"设备台账_自动导出_全部_{timestamp}.xlsx"
                export_url = f"{self.config['api_base_url']}/api/import/export/export/all"
            else:
                filename = f"设备台账_自动导出_筛选_{timestamp}.xlsx"
                export_url = f"{self.config['api_base_url']}/api/import/export/export/filtered"
                
            export_path = self.export_dir / filename
            
            self.logger.info(f"开始导出设备数据: {filename}")
            
            # 发送导出请求
            if export_type == 'filtered' and filters:
                response = self.session.post(export_url, json=filters)
            else:
                response = self.session.get(export_url)
                
            if response.status_code == 200:
                # 保存Excel文件
                with open(export_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = export_path.stat().st_size
                self.logger.info(f"导出成功: {filename} ({file_size} bytes)")
                
                # 创建导出信息文件
                info_file = export_path.with_suffix('.json')
                export_info = {
                    'timestamp': timestamp,
                    'export_type': export_type,
                    'filename': filename,
                    'file_size': file_size,
                    'filters': filters or {},
                    'exported_at': datetime.now().isoformat(),
                    'api_endpoint': export_url
                }
                
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(export_info, f, ensure_ascii=False, indent=2)
                
                return export_path
                
            else:
                raise Exception(f"导出失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"导出数据时发生错误: {e}")
            raise
            
    def cleanup_old_exports(self):
        """清理旧的导出文件"""
        self.logger.info("开始清理旧导出文件")
        
        cleaned_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
        
        for export_file in self.export_dir.glob("设备台账_自动导出_*.xlsx"):
            try:
                if export_file.stat().st_mtime < cutoff_date.timestamp():
                    export_file.unlink()
                    # 删除对应的信息文件
                    info_file = export_file.with_suffix('.json')
                    if info_file.exists():
                        info_file.unlink()
                    cleaned_count += 1
                    self.logger.info(f"删除旧导出文件: {export_file.name}")
                    
            except Exception as e:
                self.logger.warning(f"删除文件时出错 {export_file}: {e}")
                continue
                
        self.logger.info(f"清理完成，删除了 {cleaned_count} 个旧导出文件")
        return cleaned_count
        
    def get_export_status(self):
        """获取导出状态信息"""
        status = {
            'export_dir': str(self.export_dir),
            'exports': [],
            'total_exports': 0,
            'last_export': None,
            'total_size': 0,
            'retention_days': self.config['retention_days']
        }
        
        if not self.export_dir.exists():
            return status
            
        # 统计导出文件
        for export_file in self.export_dir.glob("设备台账_自动导出_*.xlsx"):
            try:
                export_info = {
                    'filename': export_file.name,
                    'size': export_file.stat().st_size,
                    'created': datetime.fromtimestamp(export_file.stat().st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(export_file.stat().st_mtime).isoformat()
                }
                
                status['exports'].append(export_info)
                status['total_exports'] += 1
                status['total_size'] += export_info['size']
                
                # 更新最后导出时间
                if status['last_export'] is None or export_info['created'] > status['last_export']:
                    status['last_export'] = export_info['created']
                    
            except Exception as e:
                self.logger.warning(f"分析导出文件时出错 {export_file}: {e}")
                continue
                
        # 按创建时间排序
        status['exports'].sort(key=lambda x: x['created'], reverse=True)
        
        return status
        
    def send_notification(self, message, subject="设备台账自动导出通知"):
        """发送通知到终端（可以扩展为邮件、webhook等）"""
        if not self.config['notification_enabled']:
            return
            
        self.logger.info(f"发送通知: {subject}")
        
        # 简单的终端通知，可以扩展为其他通知方式
        print(f"\n{'='*50}")
        print(f"📊 {subject}")
        print(f"{'='*50}")
        print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📄 消息: {message}")
        print(f"{'='*50}\n")
        
    def export_monthly_report(self):
        """导出月度报告"""
        try:
            self.logger.info("开始导出月度报告")
            
            # 获取当月第一天和最后一天
            today = datetime.now()
            first_day = today.replace(day=1)
            
            # 构建月度筛选条件
            filters = {
                'date_range': {
                    'start_date': first_day.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                },
                'status': ['在用']  # 只导出在用设备
            }
            
            # 导出数据
            export_path = self.export_equipment_data('filtered', filters)
            
            # 发送通知
            self.send_notification(
                f"月度报告导出完成，文件已保存至: {export_path}",
                f"设备台账月度报告 - {today.strftime('%Y年%m月')}"
            )
            
            return export_path
            
        except Exception as e:
            self.logger.error(f"导出月度报告失败: {e}")
            raise
            
    def export_weekly_report(self):
        """导出周度报告"""
        try:
            self.logger.info("开始导出周度报告")
            
            # 获取本周第一天（周一）
            today = datetime.now()
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            
            # 构建周度筛选条件
            filters = {
                'date_range': {
                    'start_date': monday.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                },
                'status': ['在用']  # 只导出在用设备
            }
            
            # 导出数据
            export_path = self.export_equipment_data('filtered', filters)
            
            # 发送通知
            self.send_notification(
                f"周度报告导出完成，文件已保存至: {export_path}",
                f"设备台账周度报告 - {today.strftime('%Y年第%W周')}"
            )
            
            return export_path
            
        except Exception as e:
            self.logger.error(f"导出周度报告失败: {e}")
            raise
            
    def export_daily_report(self):
        """导出日度报告"""
        try:
            self.logger.info("开始导出日度报告")
            
            # 获取当天日期
            today = datetime.now()
            
            # 构建日度筛选条件 - 当月新增设备
            filters = {
                'date_range': {
                    'start_date': today.strftime('%Y-%m-%d'),
                    'end_date': today.strftime('%Y-%m-%d')
                }
            }
            
            # 导出数据
            export_path = self.export_equipment_data('filtered', filters)
            
            # 发送通知
            self.send_notification(
                f"日度报告导出完成，文件已保存至: {export_path}",
                f"设备台账日度报告 - {today.strftime('%Y-%m-%d')}"
            )
            
            return export_path
            
        except Exception as e:
            self.logger.error(f"导出日度报告失败: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='自动Excel导出工具')
    parser.add_argument('--action', 
                       choices=['all', 'daily', 'weekly', 'monthly', 'status', 'clean'], 
                       default='all', help='执行的操作')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--export-dir', help='导出目录路径')
    parser.add_argument('--api-url', help='API基础URL')
    
    args = parser.parse_args()
    
    try:
        # 初始化导出工具
        exporter = AutoExcelExporter(args.config)
        
        # 覆盖配置参数
        if args.export_dir:
            exporter.export_dir = Path(args.export_dir)
            exporter.export_dir.mkdir(parents=True, exist_ok=True)
            
        if args.api_url:
            exporter.config['api_base_url'] = args.api_url
            
        if args.action == 'all':
            # 导出全部数据
            exporter.export_equipment_data('all')
            exporter.send_notification("全部设备数据导出完成")
            
        elif args.action == 'daily':
            # 导出日度报告
            exporter.export_daily_report()
            
        elif args.action == 'weekly':
            # 导出周度报告
            exporter.export_weekly_report()
            
        elif args.action == 'monthly':
            # 导出月度报告
            exporter.export_monthly_report()
            
        elif args.action == 'status':
            # 显示导出状态
            status = exporter.get_export_status()
            print(json.dumps(status, ensure_ascii=False, indent=2))
            
        elif args.action == 'clean':
            # 清理旧文件
            cleaned = exporter.cleanup_old_exports()
            print(f"清理完成，删除了 {cleaned} 个旧文件")
            
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()