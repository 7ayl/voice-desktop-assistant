"""File System Operations Module.

Handles all file and folder operations:
- Create files and folders
- Delete files and folders
- Copy files and folders
- Move (cut and paste) files and folders
- Search files and folders
- Rename files and folders
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from .logger import setup_logger
from config.config import Config
from .nlu_engine import ParsedCommand, OperationType, FileType

logger = setup_logger(__name__)

class FileOperationError(Exception):
    """Custom exception for file operation errors."""
    pass

class FileOperator:
    """File system operations handler."""
    
    def __init__(self):
        """Initialize File Operator."""
        self.protected_paths = Config.PROTECTED_PATHS
        logger.info("File Operator initialized")
    
    def execute(self, parsed_command: ParsedCommand) -> Dict:
        """Execute file operation based on parsed command.
        
        Args:
            parsed_command: ParsedCommand object with operation details
            
        Returns:
            Dict with execution result:
            {
                'success': bool,
                'message': str,
                'operation': str,
                'affected_items': List[str],
                'details': Dict
            }
        """
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
            logger.error(f"Unexpected error during file operation: {str(e)}")
            return {
                'success': False,
                'message': f'发生意外错误: {str(e)}',
                'operation': parsed_command.operation.value,
                'affected_items': [],
                'details': {'error': str(e)}
            }
    
    def _create(self, command: ParsedCommand) -> Dict:
        """Create a new file or folder.
        
        Args:
            command: ParsedCommand for create operation
            
        Returns:
            Operation result dict
        """
        if not command.source_name:
            raise FileOperationError("未指定文件或文件夹名称")
        
        # Determine path
        path = self._resolve_path(command.source_path, command.source_name)
        self._check_protected(path)
        
        # Check if already exists
        if os.path.exists(path):
            raise FileOperationError(f"目标已存���: {path}")
        
        # Create
        try:
            if command.file_type in [FileType.FOLDER, FileType.DIRECTORY, FileType.UNKNOWN]:
                os.makedirs(path, exist_ok=False)
                msg = f"成功创建文件夹: {command.source_name}"
                op_type = "folder"
            else:
                Path(path).touch()
                msg = f"成功创建文件: {command.source_name}"
                op_type = "file"
            
            logger.info(f"Created {op_type}: {path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'create',
                'affected_items': [path],
                'details': {
                    'path': path,
                    'type': op_type,
                    'created_at': datetime.now().isoformat()
                }
            }
        
        except OSError as e:
            raise FileOperationError(f"创建失败: {str(e)}")
    
    def _delete(self, command: ParsedCommand) -> Dict:
        """Delete a file or folder.
        
        Args:
            command: ParsedCommand for delete operation
            
        Returns:
            Operation result dict
        """
        if not command.source_name:
            raise FileOperationError("未指定文件或文件夹名称")
        
        path = self._resolve_path(command.source_path, command.source_name)
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
                msg = f"成功删除文件: {command.source_name}"
                op_type = "file"
            
            logger.info(f"Deleted {op_type}: {path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'delete',
                'affected_items': [path],
                'details': {
                    'path': path,
                    'type': op_type,
                    'deleted_at': datetime.now().isoformat()
                }
            }
        
        except OSError as e:
            raise FileOperationError(f"删除失败: {str(e)}")
    
    def _copy(self, command: ParsedCommand) -> Dict:
        """Copy a file or folder.
        
        Args:
            command: ParsedCommand for copy operation
            
        Returns:
            Operation result dict
        """
        if not command.source_name or not command.target_path:
            raise FileOperationError("未指定源文件或目标位置")
        
        source = self._resolve_path(command.source_path, command.source_name)
        target_dir = self._resolve_drive_path(command.target_path)
        self._check_protected(source)
        self._check_protected(target_dir)
        
        if not os.path.exists(source):
            raise FileOperationError(f"源文件不存在: {source}")
        
        if not os.path.exists(target_dir):
            raise FileOperationError(f"目标目录不存在: {target_dir}")
        
        target_path = os.path.join(target_dir, os.path.basename(source))
        
        try:
            if os.path.isdir(source):
                shutil.copytree(source, target_path)
                msg = f"成功复制文件夹: {command.source_name} -> {command.target_path}"
                op_type = "folder"
            else:
                shutil.copy2(source, target_path)
                msg = f"成功复制文件: {command.source_name} -> {command.target_path}"
                op_type = "file"
            
            logger.info(f"Copied {op_type}: {source} -> {target_path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'copy',
                'affected_items': [source, target_path],
                'details': {
                    'source': source,
                    'target': target_path,
                    'type': op_type,
                    'copied_at': datetime.now().isoformat()
                }
            }
        
        except (OSError, shutil.Error) as e:
            raise FileOperationError(f"复制失败: {str(e)}")
    
    def _move(self, command: ParsedCommand) -> Dict:
        """Move (cut and paste) a file or folder.
        
        Args:
            command: ParsedCommand for move operation
            
        Returns:
            Operation result dict
        """
        if not command.source_name or not command.target_path:
            raise FileOperationError("未指定源文件或目标位置")
        
        source = self._resolve_path(command.source_path, command.source_name)
        target_dir = self._resolve_drive_path(command.target_path)
        self._check_protected(source)
        self._check_protected(target_dir)
        
        if not os.path.exists(source):
            raise FileOperationError(f"源文件不存在: {source}")
        
        if not os.path.exists(target_dir):
            raise FileOperationError(f"目标目录不存在: {target_dir}")
        
        target_path = os.path.join(target_dir, os.path.basename(source))
        
        try:
            shutil.move(source, target_path)
            msg = f"成功移动: {command.source_name} -> {command.target_path}"
            op_type = "folder" if os.path.isdir(target_path) else "file"
            
            logger.info(f"Moved {op_type}: {source} -> {target_path}")
            return {
                'success': True,
                'message': msg,
                'operation': 'move',
                'affected_items': [source, target_path],
                'details': {
                    'source': source,
                    'target': target_path,
                    'type': op_type,
                    'moved_at': datetime.now().isoformat()
                }
            }
        
        except OSError as e:
            raise FileOperationError(f"移动失败: {str(e)}")
    
    def _search(self, command: ParsedCommand) -> Dict:
        """Search for files or folders.
        
        Args:
            command: ParsedCommand for search operation
            
        Returns:
            Operation result dict
        """
        if not command.source_name:
            raise FileOperationError("未指定搜索关键词")
        
        search_dir = self._resolve_drive_path(command.source_path)
        
        if not os.path.exists(search_dir):
            raise FileOperationError(f"搜索目录不存在: {search_dir}")
        
        try:
            results = self._search_recursive(search_dir, command.source_name)
            
            if results:
                msg = f"找到 {len(results)} 个包含'{command.source_name}'的项目"
                return {
                    'success': True,
                    'message': msg,
                    'operation': 'search',
                    'affected_items': results,
                    'details': {
                        'keyword': command.source_name,
                        'search_dir': search_dir,
                        'results_count': len(results),
                        'searched_at': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': True,
                    'message': f"未找到包含'{command.source_name}'的项目",
                    'operation': 'search',
                    'affected_items': [],
                    'details': {
                        'keyword': command.source_name,
                        'search_dir': search_dir,
                        'results_count': 0,
                        'searched_at': datetime.now().isoformat()
                    }
                }
        
        except Exception as e:
            raise FileOperationError(f"搜索失败: {str(e)}")
    
    def _rename(self, command: ParsedCommand) -> Dict:
        """Rename a file or folder.
        
        Args:
            command: ParsedCommand for rename operation
            
        Returns:
            Operation result dict
        """
        if not command.source_name or not command.target_name:
            raise FileOperationError("未指定原名称或新名称")
        
        source = self._resolve_path(command.source_path, command.source_name)
        target = self._resolve_path(command.source_path, command.target_name)
        self._check_protected(source)
        
        if not os.path.exists(source):
            raise FileOperationError(f"源文件不存在: {source}")
        
        if os.path.exists(target):
            raise FileOperationError(f"目标名称已存在: {target}")
        
        try:
            os.rename(source, target)
            op_type = "folder" if os.path.isdir(target) else "file"
            msg = f"成功重命名{op_type}: {command.source_name} -> {command.target_name}"
            
            logger.info(f"Renamed {op_type}: {source} -> {target}")
            return {
                'success': True,
                'message': msg,
                'operation': 'rename',
                'affected_items': [target],
                'details': {
                    'old_path': source,
                    'new_path': target,
                    'type': op_type,
                    'renamed_at': datetime.now().isoformat()
                }
            }
        
        except OSError as e:
            raise FileOperationError(f"重命名失败: {str(e)}")
    
    def _resolve_path(self, drive: Optional[str], filename: str) -> str:
        """Resolve full path from drive and filename.
        
        Args:
            drive: Drive letter (e.g., 'D:', 'D')
            filename: File or folder name
            
        Returns:
            Full path string
        """
        if not drive or drive.upper() not in [d.upper() for d in Config.DEFAULT_DRIVES]:
            drive = "D:"  # Default to D drive
        
        # Normalize drive format
        if drive and not drive.endswith(':'):
            drive = drive + ':'
        
        return os.path.join(drive, os.sep, filename)
    
    def _resolve_drive_path(self, drive: Optional[str]) -> str:
        """Resolve drive path.
        
        Args:
            drive: Drive letter (e.g., 'D:', 'D', 'E')
            
        Returns:
            Drive root path
        """
        if not drive:
            return "D:\\"
        
        if drive and not drive.endswith(':'):
            drive = drive + ':'
        
        return drive + os.sep
    
    def _check_protected(self, path: str) -> None:
        """Check if path is protected.
        
        Args:
            path: Path to check
            
        Raises:
            FileOperationError: If path is protected
        """
        path_lower = path.lower()
        for protected in self.protected_paths:
            if protected.lower() in path_lower:
                raise FileOperationError(f"无权操作受保护的路径: {path}")
    
    def _search_recursive(self, root_dir: str, keyword: str, max_results: int = 100) -> List[str]:
        """Recursively search for files/folders containing keyword.
        
        Args:
            root_dir: Root directory to search
            keyword: Search keyword
            max_results: Maximum number of results to return
            
        Returns:
            List of matching paths
        """
        results = []
        
        try:
            for root, dirs, files in os.walk(root_dir):
                # Check directories
                for dir_name in dirs:
                    if keyword.lower() in dir_name.lower():
                        results.append(os.path.join(root, dir_name))
                        if len(results) >= max_results:
                            return results
                
                # Check files
                for file_name in files:
                    if keyword.lower() in file_name.lower():
                        results.append(os.path.join(root, file_name))
                        if len(results) >= max_results:
                            return results
        
        except PermissionError:
            logger.warning(f"Permission denied when searching: {root_dir}")
        
        return results
