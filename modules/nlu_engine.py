"""Natural Language Understanding (NLU) Engine Module - 支持“X里的Y”自然语言"""

import re
import os
from typing import Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from .logger import setup_logger
from config.config import Config

logger = setup_logger(__name__)

class OperationType(Enum):
    CREATE = "create"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    SEARCH = "search"
    RENAME = "rename"
    UNKNOWN = "unknown"

class FileType(Enum):
    FILE = "file"
    FOLDER = "folder"
    UNKNOWN = "unknown"

@dataclass
class ParsedCommand:
    operation: OperationType
    file_type: FileType
    source_name: Optional[str]
    source_path: Optional[str]
    target_name: Optional[str]
    target_path: Optional[str]
    confidence: float
    raw_command: str

    def is_valid(self) -> bool:
        return (self.operation != OperationType.UNKNOWN and
                self.confidence >= Config.NLU_CONFIDENCE_THRESHOLD)


class NLUEngine:
    def __init__(self):
        logger.info("NLU Engine initialized (support 'X里的Y')")

    def parse(self, command: str) -> ParsedCommand:
        logger.info(f"Parsing command: {command}")
        cmd = command.strip('。，！？')

        # 1. 创建文件夹
        if '创建文件夹' in cmd or ('创建' in cmd and '文件夹' in cmd):
            return self._parse_create_folder(cmd)

        # 2. 创建页面
        if '创建页面' in cmd or ('创建' in cmd and '页面' in cmd):
            return self._parse_create_page(cmd)

        # 3. 删除
        if cmd.startswith('删除'):
            return self._parse_delete(cmd)

        # 4. 重命名
        if '重命名' in cmd or '改名为' in cmd:
            return self._parse_rename(cmd)

        # 5. 搜索
        if cmd.startswith('搜索') or cmd.startswith('查找'):
            return self._parse_search(cmd)

        # 6. 复制
        if cmd.startswith('复制') or cmd.startswith('拷贝'):
            return self._parse_copy(cmd)

        # 7. 移动
        if cmd.startswith('移动') or cmd.startswith('移到'):
            return self._parse_move(cmd)

        return ParsedCommand(OperationType.UNKNOWN, FileType.UNKNOWN,
                             None, None, None, None, 0.0, command)

    def _parse_create_folder(self, cmd: str) -> ParsedCommand:
        match = re.search(r'创建文件夹\s*([^\s，。]+)', cmd)
        if match:
            name = match.group(1)
        else:
            match = re.search(r'在(?:桌面|文档|下载)?创建文件夹[，,]*\s*([^\s，。]+)', cmd)
            name = match.group(1) if match else "新文件夹"
        location = "桌面"
        source_path = self._to_abs_path(location)
        return ParsedCommand(
            operation=OperationType.CREATE,
            file_type=FileType.FOLDER,
            source_name=name,
            source_path=source_path,
            target_name=None, target_path=None,
            confidence=0.95, raw_command=cmd
        )

    def _parse_create_page(self, cmd: str) -> ParsedCommand:
        match = re.search(r'在([^\s]+?)里面?创建(?:一个)?页面([^\s，。！？]+)', cmd)
        if match:
            location = match.group(1)
            name = match.group(2)
        else:
            name = "新页面"
            location = "桌面"
        if location not in ['桌面','文档','下载']:
            source_path = os.path.join(os.path.expanduser("~/Desktop"), location)
        else:
            source_path = self._to_abs_path(location)
        return ParsedCommand(
            operation=OperationType.CREATE,
            file_type=FileType.FILE,
            source_name=name,
            source_path=source_path,
            target_name=None, target_path=None,
            confidence=0.95, raw_command=cmd
        )

    def _parse_delete(self, cmd: str) -> ParsedCommand:
        # 移除常见的修饰词（包括“桌面上的”、“的”等），但要保留核心名称
        # 先用正则提取出目标名称：删除后面的内容，直到遇到结尾或“文件夹/页面”
        import re
        # 匹配 "删除" 后面的非空格部分（可能含有中文、字母、数字）
        match = re.search(r'删除\s*([^\s]+?)(?:文件夹|页面)?$', cmd)
        if not match:
            # 再尝试匹配带“桌面上的”等前缀的情况
            match = re.search(r'删除\s*(?:桌面上的|里的)?\s*([^\s]+?)(?:文件夹|页面)?$', cmd)
        if match:
            target = match.group(1).strip()
        else:
            return ParsedCommand(OperationType.UNKNOWN, FileType.UNKNOWN, None, None, None, None, 0.0, cmd)
        # 去除可能残留的“文件夹”或“页面”（实际上正则已处理，但安全起见）
        for word in ['文件夹', '页面']:
            target = target.replace(word, '')
        if not target:
            return ParsedCommand(OperationType.UNKNOWN, FileType.UNKNOWN, None, None, None, None, 0.0, cmd)
        # 判断是否包含路径分隔符
        if '/' in target or '\\' in target:
            source_path = os.path.dirname(target)
            source_name = os.path.basename(target)
        else:
            source_name = target
            source_path = os.path.expanduser("~/Desktop")
        return ParsedCommand(
            operation=OperationType.DELETE,
            file_type=FileType.UNKNOWN,
            source_name=source_name,
            source_path=source_path,
            target_name=None, target_path=None,
            confidence=0.95, raw_command=cmd
        )

    def _parse_rename(self, cmd: str) -> ParsedCommand:
        match = re.search(r'(?:重命名|把)\s*([^\s]+)\s*(?:为|重命名为)\s*([^\s]+)', cmd)
        if match:
            old = match.group(1)
            new = match.group(2)
        else:
            return ParsedCommand(OperationType.UNKNOWN, FileType.UNKNOWN, None, None, None, None, 0.0, cmd)
        return ParsedCommand(
            operation=OperationType.RENAME,
            file_type=FileType.FOLDER,
            source_name=old,
            source_path=os.path.expanduser("~/Desktop"),
            target_name=new,
            target_path=None,
            confidence=0.95, raw_command=cmd
        )

    def _parse_search(self, cmd: str) -> ParsedCommand:
        match = re.search(r'(?:查找|搜索)\s*([^\s]+)\s*在\s*([^\s]+)', cmd)
        if match:
            keyword = match.group(1)
            location = match.group(2)
        else:
            keyword = cmd.split()[-1] if len(cmd.split()) > 1 else ""
            location = "桌面"
        if location not in ['桌面','文档','下载']:
            location = os.path.join(os.path.expanduser("~/Desktop"), location)
        else:
            location = self._to_abs_path(location)
        return ParsedCommand(
            operation=OperationType.SEARCH,
            file_type=FileType.UNKNOWN,
            source_name=keyword,
            source_path=location,
            target_name=None, target_path=None,
            confidence=0.95, raw_command=cmd
        )

    def _parse_copy(self, cmd: str) -> ParsedCommand:
        # 优先匹配 "复制 X里的Y 到 Z" 模式
        match = re.search(r'复制\s*([^\s]+?)里(?:面)?的?\s*([^\s]+?)\s*到\s*([^\s]+)', cmd)
        if match:
            folder = match.group(1).strip()
            item = match.group(2).strip()
            target = match.group(3).strip()
            # source_name 是项目名，source_path 是文件夹名（相对桌面）
            return ParsedCommand(
                operation=OperationType.COPY,
                file_type=FileType.UNKNOWN,
                source_name=item,
                source_path=folder,      # 文件夹名，稍后在 file_operator 中解析
                target_name=None,
                target_path=target,
                confidence=0.95,
                raw_command=cmd
            )
        # 后备模式：复制 a/b 到 c
        match = re.search(r'复制\s*([^\s]+)\s*到\s*([^\s]+)', cmd)
        if match:
            source = match.group(1)
            target = match.group(2)
            if '/' in source or '\\' in source:
                source_path = os.path.dirname(source)
                source_name = os.path.basename(source)
            else:
                source_name = source
                source_path = "桌面"
            target_path = self._to_abs_path(target)
            return ParsedCommand(
                operation=OperationType.COPY,
                file_type=FileType.FILE,
                source_name=source_name,
                source_path=source_path,
                target_name=None,
                target_path=target_path,
                confidence=0.9,
                raw_command=cmd
            )
        return ParsedCommand(OperationType.UNKNOWN, FileType.UNKNOWN, None, None, None, None, 0.0, cmd)

    def _parse_move(self, cmd: str) -> ParsedCommand:
        # 优先匹配 "移动 X里的Y 到 Z"
        match = re.search(r'移动\s*([^\s]+?)里(?:面)?的?\s*([^\s]+?)\s*到\s*([^\s]+)', cmd)
        if match:
            folder = match.group(1).strip()
            item = match.group(2).strip()
            target = match.group(3).strip()
            return ParsedCommand(
                operation=OperationType.MOVE,
                file_type=FileType.UNKNOWN,
                source_name=item,
                source_path=folder,
                target_name=None,
                target_path=target,
                confidence=0.95,
                raw_command=cmd
            )
        match = re.search(r'移动\s*([^\s]+)\s*到\s*([^\s]+)', cmd)
        if match:
            source = match.group(1)
            target = match.group(2)
            if '/' in source or '\\' in source:
                source_path = os.path.dirname(source)
                source_name = os.path.basename(source)
            else:
                source_name = source
                source_path = "桌面"
            target_path = self._to_abs_path(target)
            return ParsedCommand(
                operation=OperationType.MOVE,
                file_type=FileType.FILE,
                source_name=source_name,
                source_path=source_path,
                target_name=None,
                target_path=target_path,
                confidence=0.9,
                raw_command=cmd
            )
        return ParsedCommand(OperationType.UNKNOWN, FileType.UNKNOWN, None, None, None, None, 0.0, cmd)

    def _to_abs_path(self, location: str) -> str:
        if location == '桌面':
            return os.path.expanduser("~/Desktop")
        elif location == '文档':
            return os.path.expanduser("~/Documents")
        elif location == '下载':
            return os.path.expanduser("~/Downloads")
        else:
            return location if os.path.isabs(location) else os.path.join(os.path.expanduser("~/Desktop"), location)