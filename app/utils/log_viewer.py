#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志查看工具
提供日志文件的查看、搜索和分析功能
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

class LogViewer:
    """日志查看器"""
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
    
    def get_log_files(self) -> List[str]:
        """获取所有日志文件"""
        if not self.log_dir.exists():
            return []
        
        log_files = []
        for file in self.log_dir.glob("*.log"):
            log_files.append(str(file))
        for file in self.log_dir.glob("*.json"):
            log_files.append(str(file))
        
        return sorted(log_files)
    
    def read_log_file(self, file_path: str, lines: int = 100) -> List[str]:
        """读取日志文件的最后N行"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            return [f"读取文件失败: {str(e)}"]
    
    def search_logs(
        self, 
        keyword: str, 
        log_type: str = "all",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """搜索日志"""
        results = []
        
        # 确定要搜索的文件
        if log_type == "all":
            files = self.get_log_files()
        elif log_type == "json":
            files = list(self.log_dir.glob("*.json"))
        else:
            files = [self.log_dir / f"{log_type}.log"]
        
        for file_path in files:
            if not Path(file_path).exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            # 尝试解析JSON格式的日志
                            log_entry = self._parse_log_line(line, str(file_path), line_num)
                            
                            # 时间过滤
                            if start_time or end_time:
                                log_time = log_entry.get('timestamp')
                                if log_time:
                                    try:
                                        log_datetime = datetime.fromisoformat(log_time.replace('Z', '+00:00'))
                                        if start_time and log_datetime < start_time:
                                            continue
                                        if end_time and log_datetime > end_time:
                                            continue
                                    except:
                                        pass
                            
                            results.append(log_entry)
                            
                            if len(results) >= max_results:
                                return results
            except Exception as e:
                results.append({
                    'file': str(file_path),
                    'line': 0,
                    'content': f"读取文件失败: {str(e)}",
                    'timestamp': datetime.now().isoformat(),
                    'level': 'ERROR'
                })
        
        return results
    
    def _parse_log_line(self, line: str, file_path: str, line_num: int) -> Dict[str, Any]:
        """解析日志行"""
        line = line.strip()
        
        # 尝试解析JSON格式
        if line.startswith('{'):
            try:
                json_data = json.loads(line)
                json_data['file'] = file_path
                json_data['line'] = line_num
                return json_data
            except:
                pass
        
        # 解析普通格式的日志
        # 格式: 2024-01-01 12:00:00,000 - logger_name - LEVEL - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - ([^-]+) - (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp, logger_name, level, message = match.groups()
            return {
                'timestamp': timestamp.strip(),
                'logger': logger_name.strip(),
                'level': level.strip(),
                'message': message.strip(),
                'file': file_path,
                'line': line_num,
                'content': line
            }
        
        # 如果无法解析，返回原始内容
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'UNKNOWN',
            'message': line,
            'file': file_path,
            'line': line_num,
            'content': line
        }
    
    def get_error_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近N小时的错误日志"""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.search_logs("ERROR", start_time=start_time)
    
    def get_security_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近N小时的安全日志"""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.search_logs("security_event", start_time=start_time)
    
    def get_api_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近N小时的API日志"""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.search_logs("api_request", start_time=start_time)
    
    def analyze_logs(self, hours: int = 24) -> Dict[str, Any]:
        """分析日志统计信息"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        # 获取所有日志
        all_logs = self.search_logs("", start_time=start_time, max_results=10000)
        
        # 统计信息
        stats = {
            'total_logs': len(all_logs),
            'by_level': {},
            'by_logger': {},
            'by_hour': {},
            'errors': 0,
            'warnings': 0,
            'api_requests': 0,
            'security_events': 0
        }
        
        for log in all_logs:
            level = log.get('level', 'UNKNOWN')
            logger = log.get('logger', 'unknown')
            action = log.get('action', '')
            
            # 按级别统计
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            
            # 按日志记录器统计
            stats['by_logger'][logger] = stats['by_logger'].get(logger, 0) + 1
            
            # 特殊事件统计
            if level == 'ERROR':
                stats['errors'] += 1
            elif level == 'WARNING':
                stats['warnings'] += 1
            
            if action == 'api_request':
                stats['api_requests'] += 1
            elif action == 'security_event':
                stats['security_events'] += 1
            
            # 按小时统计
            timestamp = log.get('timestamp', '')
            if timestamp:
                try:
                    if 'T' in timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = datetime.strptime(timestamp.split(',')[0], '%Y-%m-%d %H:%M:%S')
                    
                    hour_key = dt.strftime('%Y-%m-%d %H:00')
                    stats['by_hour'][hour_key] = stats['by_hour'].get(hour_key, 0) + 1
                except:
                    pass
        
        return stats
    
    def tail_log(self, file_path: str, lines: int = 50) -> List[str]:
        """实时查看日志文件末尾"""
        return self.read_log_file(file_path, lines)

def main():
    """命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description='日志查看工具')
    parser.add_argument('--search', '-s', help='搜索关键词')
    parser.add_argument('--type', '-t', default='all', help='日志类型 (all, json, app, error)')
    parser.add_argument('--hours', '-h', type=int, default=24, help='查看最近N小时的日志')
    parser.add_argument('--lines', '-l', type=int, default=100, help='显示行数')
    parser.add_argument('--analyze', '-a', action='store_true', help='分析日志统计')
    parser.add_argument('--errors', '-e', action='store_true', help='只显示错误日志')
    parser.add_argument('--security', action='store_true', help='只显示安全日志')
    parser.add_argument('--api', action='store_true', help='只显示API日志')
    
    args = parser.parse_args()
    
    viewer = LogViewer()
    
    if args.analyze:
        stats = viewer.analyze_logs(args.hours)
        print("=== 日志统计分析 ===")
        print(f"总日志数: {stats['total_logs']}")
        print(f"错误数: {stats['errors']}")
        print(f"警告数: {stats['warnings']}")
        print(f"API请求数: {stats['api_requests']}")
        print(f"安全事件数: {stats['security_events']}")
        print("\n按级别统计:")
        for level, count in stats['by_level'].items():
            print(f"  {level}: {count}")
        print("\n按记录器统计:")
        for logger, count in stats['by_logger'].items():
            print(f"  {logger}: {count}")
        return
    
    if args.errors:
        logs = viewer.get_error_logs(args.hours)
        print(f"=== 最近{args.hours}小时的错误日志 ===")
    elif args.security:
        logs = viewer.get_security_logs(args.hours)
        print(f"=== 最近{args.hours}小时的安全日志 ===")
    elif args.api:
        logs = viewer.get_api_logs(args.hours)
        print(f"=== 最近{args.hours}小时的API日志 ===")
    elif args.search:
        start_time = datetime.now() - timedelta(hours=args.hours)
        logs = viewer.search_logs(args.search, args.type, start_time=start_time, max_results=args.lines)
        print(f"=== 搜索结果: '{args.search}' ===")
    else:
        # 显示最新的日志
        log_files = viewer.get_log_files()
        if not log_files:
            print("没有找到日志文件")
            return
        
        latest_file = max(log_files, key=lambda f: os.path.getmtime(f))
        lines = viewer.tail_log(latest_file, args.lines)
        print(f"=== {latest_file} (最后{len(lines)}行) ===")
        for line in lines:
            print(line.rstrip())
        return
    
    # 显示日志
    for log in logs:
        timestamp = log.get('timestamp', 'N/A')
        level = log.get('level', 'N/A')
        message = log.get('message', log.get('content', 'N/A'))
        print(f"[{timestamp}] {level}: {message}")

if __name__ == "__main__":
    main()