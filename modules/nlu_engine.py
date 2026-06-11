"""Natural Language Understanding (NLU) Engine Module.

Parses user commands and extracts intent and parameters.
Supports file operation commands in Chinese.
"""

import re
from typing import Dict, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass
from .logger import setup_logger
from config.config import Config

logger = setup_logger(__name__)

class OperationType(Enum):
    """Supported file operation types."""
    CREATE = "create"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    SEARCH = "search"
    RENAME = "rename"
    UNKNOWN = "unknown"

class FileType(Enum):
    """Target file types."""
    FILE = "file"
    FOLDER = "folder"
    DIRECTORY = "directory"
    UNKNOWN = "unknown"

@dataclass
class ParsedCommand:
    """Represents a parsed user command."""
    operation: OperationType
    file_type: FileType
    source_name: Optional[str]
    source_path: Optional[str]
    target_name: Optional[str]
    target_path: Optional[str]
    confidence: float
    raw_command: str
    
    def is_valid(self) -> bool:
        """Check if command is valid for execution.
        
        Returns:
            True if command has sufficient information
        """
        return (
            self.operation != OperationType.UNKNOWN and
            self.confidence >= Config.NLU_CONFIDENCE_THRESHOLD
        )

class CommandPattern:
    """Pattern matcher for command parsing."""
    
    # Chinese patterns for different operations
    PATTERNS = {
        OperationType.CREATE: [
            r'(?:帮我)?(?:在)?([A-Za-z]:)?(?:盘)?(?:创建|新建)(?:一个)?(?:名称?[为是])?["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:的)?(?:文件夹|目录|文件)?',
            r'(?:创建|新建)(?:文件夹|目录)?["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:在)?([A-Za-z]:)?(?:盘)?',
        ],
        OperationType.DELETE: [
            r'(?:帮我)?(?:删除|移除)([A-Za-z]:)?(?:盘)?(?:里)?(?:的)?(?:名称?[为是])?["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:的)?(?:文件夹|目录|文件)?',
            r'(?:删除|移除)["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:在)?([A-Za-z]:)?(?:盘)?',
        ],
        OperationType.COPY: [
            r'(?:帮我)?(?:把|将)([A-Za-z]:)?(?:盘)?(?:里)?(?:的)?(?:名称?[为是])?["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:复制|拷贝)(?:到|在)?([A-Za-z]:)?(?:盘)?',
            r'(?:复制|拷贝)["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:到|在)?([A-Za-z]:)?(?:盘)?',
        ],
        OperationType.MOVE: [
            r'(?:帮我)?(?:把|将)([A-Za-z]:)?(?:盘)?(?:里)?(?:的)?(?:名称?[为是])?["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:移到|移动到|移|去)?([A-Za-z]:)?(?:盘)?',
            r'(?:移动|移到)["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:到|在)?([A-Za-z]:)?(?:盘)?',
        ],
        OperationType.SEARCH: [
            r'(?:帮我)?(?:在)([A-Za-z]:)?(?:盘)?(?:查找|搜索|寻找)(?:是否有)?(?:名称)?(?:包含)?["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:的)?(?:文件|目录)?',
            r'(?:查找|搜索|寻找)["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:在)?([A-Za-z]:)?(?:盘)?',
        ],
        OperationType.RENAME: [
            r'(?:帮我)?(?:把|将)([A-Za-z]:)?(?:盘)?(?:里)?(?:的)?(?:名称?[为是])?["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:改?(?:名)?(?:为|成))\s*["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*',
            r'(?:重命名|改名)["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*(?:为|成)["\'\'\"]*([^\\/:*?"<>|\n]+)["\'\'\"]*',
        ],
    }
    
    @classmethod
    def match_patterns(cls, command: str, operation_type: OperationType) -> Optional[Tuple[float, Dict]]:
        """Match command against patterns for an operation type.
        
        Args:
            command: User command text
            operation_type: Target operation type
            
        Returns:
            Tuple of (confidence, match_groups) or None if no match
        """
        patterns = cls.PATTERNS.get(operation_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                # Extract groups and calculate confidence
                groups = match.groups()
                confidence = 0.85 + (0.1 * len([g for g in groups if g]))
                confidence = min(confidence, 0.99)
                
                return confidence, {'groups': groups, 'span': match.span()}
        
        return None

class NLUEngine:
    """Natural Language Understanding Engine for command parsing."""
    
    def __init__(self):
        """Initialize NLU Engine."""
        self.operation_keywords = {
            OperationType.CREATE: ['创建', '新建', '建立'],
            OperationType.DELETE: ['删除', '移除', '清除', '摧毁'],
            OperationType.COPY: ['复制', '拷贝', '备份'],
            OperationType.MOVE: ['移动', '移到', '移入', '转移'],
            OperationType.SEARCH: ['查找', '搜索', '寻找', '查询'],
            OperationType.RENAME: ['改名', '重命名', '改成', '改为'],
        }
        logger.info("NLU Engine initialized")
    
    def parse(self, command: str) -> 'ParsedCommand':
        """Parse user command into structured format.
        
        Args:
            command: User input command text
            
        Returns:
            ParsedCommand object with extracted information
        """
        logger.info(f"Parsing command: {command}")
        
        # Detect operation type
        operation_type = self._detect_operation(command)
        
        # Try to match patterns
        match_result = CommandPattern.match_patterns(command, operation_type)
        
        if match_result:
            confidence, match_data = match_result
            groups = match_data['groups']
            
            # Extract information based on operation type
            parsed = self._extract_info(
                command=command,
                operation=operation_type,
                groups=groups,
                confidence=confidence
            )
        else:
            # Fallback parsing
            parsed = ParsedCommand(
                operation=OperationType.UNKNOWN,
                file_type=FileType.UNKNOWN,
                source_name=None,
                source_path=None,
                target_name=None,
                target_path=None,
                confidence=0.0,
                raw_command=command
            )
        
        logger.info(f"Parsed command: operation={parsed.operation.value}, "
                   f"source={parsed.source_name}, target={parsed.target_name}, "
                   f"confidence={parsed.confidence}")
        
        return parsed
    
    def _detect_operation(self, command: str) -> OperationType:
        """Detect operation type from command keywords.
        
        Args:
            command: User command
            
        Returns:
            Detected OperationType
        """
        command_lower = command.lower()
        
        for op_type, keywords in self.operation_keywords.items():
            for keyword in keywords:
                if keyword in command:
                    return op_type
        
        return OperationType.UNKNOWN
    
    def _extract_info(self, command: str, operation: OperationType, 
                      groups: Tuple, confidence: float) -> ParsedCommand:
        """Extract detailed information from matched groups.
        
        Args:
            command: Original command
            operation: Detected operation type
            groups: Regex match groups
            confidence: Match confidence score
            
        Returns:
            ParsedCommand with extracted information
        """
        source_name = None
        source_path = None
        target_name = None
        target_path = None
        file_type = self._detect_file_type(command)
        
        # Extract information based on operation type
        if operation == OperationType.CREATE:
            source_path = groups[0] if len(groups) > 0 else None
            source_name = groups[1] if len(groups) > 1 else None
        
        elif operation == OperationType.DELETE:
            source_path = groups[0] if len(groups) > 0 else None
            source_name = groups[1] if len(groups) > 1 else None
        
        elif operation == OperationType.COPY:
            source_path = groups[0] if len(groups) > 0 else None
            source_name = groups[1] if len(groups) > 1 else None
            target_path = groups[2] if len(groups) > 2 else None
        
        elif operation == OperationType.MOVE:
            source_path = groups[0] if len(groups) > 0 else None
            source_name = groups[1] if len(groups) > 1 else None
            target_path = groups[2] if len(groups) > 2 else None
        
        elif operation == OperationType.SEARCH:
            source_path = groups[0] if len(groups) > 0 else None
            source_name = groups[1] if len(groups) > 1 else None
        
        elif operation == OperationType.RENAME:
            source_path = groups[0] if len(groups) > 0 else None
            source_name = groups[1] if len(groups) > 1 else None
            target_name = groups[2] if len(groups) > 2 else None
        
        return ParsedCommand(
            operation=operation,
            file_type=file_type,
            source_name=source_name,
            source_path=source_path,
            target_name=target_name,
            target_path=target_path,
            confidence=confidence,
            raw_command=command
        )
    
    def _detect_file_type(self, command: str) -> FileType:
        """Detect whether command refers to file or folder.
        
        Args:
            command: User command
            
        Returns:
            Detected FileType
        """
        folder_keywords = ['文件夹', '目录', '文件夹']
        file_keywords = ['文件', '文本']
        
        for keyword in folder_keywords:
            if keyword in command:
                return FileType.FOLDER
        
        for keyword in file_keywords:
            if keyword in command:
                return FileType.FILE
        
        return FileType.UNKNOWN
