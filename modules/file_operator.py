"""File System Operations Module - 支持自动查找和“X里的Y”操作"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .logger import setup_logger
from config.config import Config
from .nlu_engine import ParsedCommand, OperationType, FileType

logger = setup_logger(__name__)

class FileOperationError(Exception):
    pass

class FileOperator:
    def __init__(self):
        self.protected_paths = Config.PROTECTED_PATHS
        logger.info("File Operator initialized")

    def execute(self, parsed_command: ParsedCommand) -> Dict:
        try:
            if not parsed_command.is_valid():
                return {
                    'success': False,
                    'message': f'命令置信度过低 ({parsed_command.confidence:.2f}), 请重新说一遍',
                    'operation': parsed_command.operation.value,
                    'affected_items': [],
                    'details': {}
                }
            operation = parsed_command.operation
            if operation == OperationType.CREATE:
                return self._create(parsed_command)
            elif operation == OperationType.DELETE:
                return self._delete(parsed_command)
            elif operation == OperationType.COPY:
                return self._copy(parsed_command)
            elif operation == OperationType.MOVE:
                return self._move(parsed_command)
            elif operation == OperationType.SEARCH:
                return self._search(parsed_command)
            elif operation == OperationType.RENAME:
                return self._rename(parsed_command)
            else:
                return {
                    'success': False,
                    'message': '无法识别的操作类型',
                    'operation': 'unknown',
                    'affected_items': [],
                    'details': {}
                }
        except FileOperationError as e:
            logger.error(f"File operation error: {str(e)}")
            return {
                'success': False,
                'message': f'操作失败: {str(e)}',
                'operation': parsed_command.operation.value,
                'affected_items': [],
                'details': {'error': str(e)}
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'message': f'发生意外错误: {str(e)}',
                'operation': parsed_command.operation.value,
                'affected_items': [],
                'details': {'error': str(e)}
            }

    def _find_item(self, name: str, start_dir: Optional[str] = None) -> Optional[str]:
        """在 start_dir（默认桌面）及其子目录中递归查找名称为 name 的文件或文件夹，返回第一个匹配的绝对路径。"""
        if start_dir is None:
            start_dir = os.path.expanduser("~/Desktop")
        if not os.path.exists(start_dir):
            return None
        for root, dirs, files in os.walk(start_dir):
            if name in dirs:
                return os.path.join(root, name)
            if name in files:
                return os.path.join(root, name)
        return None

    def _create(self, command: ParsedCommand) -> Dict:
        if not command.source_name:
            raise FileOperationError("未指定文件或文件夹名称")

        if command.file_type == FileType.FILE:
            filename = command.source_name
            if not filename.endswith('.txt'):
                filename += '.txt'
        else:
            filename = command.source_name

        path = self._resolve_path(command.source_path, filename)
        self._check_protected(path)
        if os.path.exists(path):
            raise FileOperationError(f"目标已存在: {path}")
        try:
            if command.file_type == FileType.FOLDER:
                os.makedirs(path, exist_ok=False)
                msg = f"成功创建文件夹: {command.source_name}"
                op_type = "folder"
            else:
                parent_dir = os.path.dirname(path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                Path(path).touch()
                msg = f"成功创建页面: {filename}"
                op_type = "file"
            logger.info(f"Created {op_type}: {path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'create',
                'affected_items': [path],
                'details': {'path': path, 'type': op_type, 'created_at': datetime.now().isoformat()}
            }
        except OSError as e:
            raise FileOperationError(f"创建失败: {str(e)}")

    def _delete(self, command: ParsedCommand) -> Dict:
        if not command.source_name:
            raise FileOperationError("未指定文件或文件夹名称")
        if command.source_path and os.path.isabs(command.source_path):
            base = command.source_path
        else:
            base = self._resolve_drive_path(command.source_path) if command.source_path else os.path.expanduser("~/Desktop")
        path = os.path.join(base, command.source_name)
        if command.file_type == FileType.FILE and not command.source_name.endswith('.txt'):
            if not os.path.exists(path):
                alt_path = path + '.txt'
                if os.path.exists(alt_path):
                    path = alt_path
        self._check_protected(path)
        if not os.path.exists(path):
            raise FileOperationError(f"文件不存在: {path}")
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                msg = f"成功删除文件夹: {command.source_name}"
                op_type = "folder"
            else:
                os.remove(path)
                msg = f"成功删除页面: {command.source_name}"
                op_type = "file"
            logger.info(f"Deleted {op_type}: {path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'delete',
                'affected_items': [path],
                'details': {'path': path, 'type': op_type, 'deleted_at': datetime.now().isoformat()}
            }
        except OSError as e:
            raise FileOperationError(f"删除失败: {str(e)}")

    def _copy(self, command: ParsedCommand) -> Dict:
        if not command.source_name or not command.target_path:
            raise FileOperationError("未指定源文件或目标位置")
        # 确定源文件位置
        source_full = None
        # 如果 source_path 不是绝对路径，且不是“桌面”等关键词，视为文件夹名
        if command.source_path and command.source_path not in ['桌面','文档','下载'] and not os.path.isabs(command.source_path):
            # 先尝试在桌面上找到该文件夹
            folder_abs = self._find_item(command.source_path)
            if folder_abs and os.path.isdir(folder_abs):
                # 在文件夹内查找 source_name
                candidate = os.path.join(folder_abs, command.source_name)
                if os.path.exists(candidate):
                    source_full = candidate
                else:
                    # 尝试加 .txt
                    if not command.source_name.endswith('.txt'):
                        candidate_txt = candidate + '.txt'
                        if os.path.exists(candidate_txt):
                            source_full = candidate_txt
            if not source_full:
                # 没找到文件夹或文件，尝试全局查找 source_name
                found = self._find_item(command.source_name)
                if found:
                    source_full = found
        else:
            # 原有逻辑：直接拼接
            source_full = self._resolve_path(command.source_path, command.source_name)
            if not os.path.exists(source_full) and not source_full.endswith('.txt'):
                alt = source_full + '.txt'
                if os.path.exists(alt):
                    source_full = alt
        if not source_full or not os.path.exists(source_full):
            raise FileOperationError(f"源文件不存在: {command.source_name} (在文件夹 {command.source_path} 中未找到)")

        target_dir = self._resolve_drive_path(command.target_path)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, os.path.basename(source_full))
        try:
            if os.path.isdir(source_full):
                shutil.copytree(source_full, target_path)
            else:
                shutil.copy2(source_full, target_path)
            msg = f"成功复制: {command.source_name} -> {command.target_path}"
            logger.info(f"Copied: {source_full} -> {target_path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'copy',
                'affected_items': [source_full, target_path],
                'details': {'source': source_full, 'target': target_path}
            }
        except Exception as e:
            raise FileOperationError(f"复制失败: {str(e)}")

    def _move(self, command: ParsedCommand) -> Dict:
        if not command.source_name or not command.target_path:
            raise FileOperationError("未指定源文件或目标位置")
        source_full = None
        if command.source_path and command.source_path not in ['桌面','文档','下载'] and not os.path.isabs(command.source_path):
            folder_abs = self._find_item(command.source_path)
            if folder_abs and os.path.isdir(folder_abs):
                candidate = os.path.join(folder_abs, command.source_name)
                if os.path.exists(candidate):
                    source_full = candidate
                else:
                    if not command.source_name.endswith('.txt'):
                        candidate_txt = candidate + '.txt'
                        if os.path.exists(candidate_txt):
                            source_full = candidate_txt
            if not source_full:
                found = self._find_item(command.source_name)
                if found:
                    source_full = found
        else:
            source_full = self._resolve_path(command.source_path, command.source_name)
            if not os.path.exists(source_full) and not source_full.endswith('.txt'):
                alt = source_full + '.txt'
                if os.path.exists(alt):
                    source_full = alt
        if not source_full or not os.path.exists(source_full):
            raise FileOperationError(f"源文件不存在: {command.source_name} (在文件夹 {command.source_path} 中未找到)")

        target_dir = self._resolve_drive_path(command.target_path)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, os.path.basename(source_full))
        if source_full == target_dir or source_full == target_path:
            raise FileOperationError("不能将文件/文件夹移动到自己内部")
        if os.path.commonpath([source_full, target_dir]) == source_full:
            raise FileOperationError("不能将文件夹移动到其自身的子文件夹中")
        try:
            shutil.move(source_full, target_path)
            msg = f"成功移动: {command.source_name} -> {command.target_path}"
            logger.info(f"Moved: {source_full} -> {target_path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'move',
                'affected_items': [source_full, target_path],
                'details': {'source': source_full, 'target': target_path}
            }
        except Exception as e:
            raise FileOperationError(f"移动失败: {str(e)}")

    def _search(self, command: ParsedCommand) -> Dict:
        if not command.source_name:
            raise FileOperationError("未指定搜索关键词")
        search_dir = self._resolve_drive_path(command.source_path) if command.source_path else os.path.expanduser("~")
        if not os.path.exists(search_dir):
            raise FileOperationError(f"搜索目录不存在: {search_dir}")
        try:
            results = []
            for root, dirs, files in os.walk(search_dir):
                for name in dirs + files:
                    if command.source_name.lower() in name.lower():
                        results.append(os.path.join(root, name))
                        if len(results) >= 50:
                            break
                if len(results) >= 50:
                    break
            if results:
                msg = f"找到 {len(results)} 个包含 '{command.source_name}' 的项目"
            else:
                msg = f"未找到包含 '{command.source_name}' 的项目"
            return {
                'success': True,
                'message': msg,
                'operation': 'search',
                'affected_items': results,
                'details': {'keyword': command.source_name, 'search_dir': search_dir, 'count': len(results)}
            }
        except Exception as e:
            raise FileOperationError(f"搜索失败: {str(e)}")

    def _rename(self, command: ParsedCommand) -> Dict:
        if not command.source_name or not command.target_name:
            raise FileOperationError("未指定原名称或新名称")
        source = self._resolve_path(command.source_path, command.source_name)
        if not os.path.exists(source) and not source.endswith('.txt'):
            alt_source = source + '.txt'
            if os.path.exists(alt_source):
                source = alt_source
        if command.file_type == FileType.FILE and not command.target_name.endswith('.txt'):
            new_name = command.target_name + '.txt'
        else:
            new_name = command.target_name
        target = self._resolve_path(command.source_path, new_name)
        if not os.path.exists(source):
            raise FileOperationError(f"源文件不存在: {source}")
        if os.path.exists(target):
            raise FileOperationError(f"目标名称已存在: {target}")
        try:
            os.rename(source, target)
            msg = f"成功重命名: {command.source_name} -> {command.target_name}"
            logger.info(f"Renamed: {source} -> {target}")
            return {
                'success': True,
                'message': msg,
                'operation': 'rename',
                'affected_items': [target],
                'details': {'old': source, 'new': target}
            }
        except OSError as e:
            raise FileOperationError(f"重命名失败: {str(e)}")

    def _resolve_path(self, location: Optional[str], filename: str) -> str:
        if not location:
            location = "桌面"
        base = self._resolve_drive_path(location)
        return os.path.join(base, filename)

    def _resolve_drive_path(self, location: Optional[str]) -> str:
        if not location:
            location = "桌面"
        location_map = {
            "桌面": os.path.expanduser("~/Desktop"),
            "文档": os.path.expanduser("~/Documents"),
            "下载": os.path.expanduser("~/Downloads"),
        }
        if location in location_map:
            return location_map[location]
        if os.path.isabs(location):
            return location
        return os.path.join(os.path.expanduser("~/Desktop"), location)

    def _check_protected(self, path: str) -> None:
        path_lower = path.lower()
        for protected in self.protected_paths:
            if protected.lower() in path_lower:
                raise FileOperationError(f"无权操作受保护的路径: {path}")