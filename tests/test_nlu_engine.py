"""Unit tests for NLU Engine."""

import unittest
from modules.nlu_engine import NLUEngine, OperationType, FileType

class TestNLUEngine(unittest.TestCase):
    """Test cases for Natural Language Understanding Engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.nlu = NLUEngine()
    
    # Test CREATE operations
    def test_create_folder_in_d_drive(self):
        """Test creating a folder in D drive."""
        command = "帮我在D盘创建一个名称为'我的作业'的文件夹"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.CREATE)
        self.assertIsNotNone(result.source_name)
        self.assertIsNotNone(result.source_path)
        self.assertTrue(result.is_valid())
    
    def test_create_file(self):
        """Test creating a file."""
        command = "创建一个名叫test的文件"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.CREATE)
    
    # Test DELETE operations
    def test_delete_folder(self):
        """Test deleting a folder."""
        command = "帮我删除D盘里名称为'oldfile'的文件夹"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.DELETE)
        self.assertIsNotNone(result.source_name)
    
    def test_delete_file(self):
        """Test deleting a file."""
        command = "在E盘删除'temp'文件"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.DELETE)
    
    # Test COPY operations
    def test_copy_file_to_drive(self):
        """Test copying a file to another drive."""
        command = "帮我把D盘的'我的考试'复制到E盘"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.COPY)
        self.assertIsNotNone(result.source_name)
        self.assertIsNotNone(result.target_path)
    
    def test_copy_folder(self):
        """Test copying a folder."""
        command = "复制D盘的'project'文件夹到F盘"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.COPY)
    
    # Test MOVE operations
    def test_move_folder(self):
        """Test moving a folder."""
        command = "帮我把D盘里的'我的文档'移到E盘"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.MOVE)
        self.assertIsNotNone(result.source_name)
        self.assertIsNotNone(result.target_path)
    
    def test_move_file(self):
        """Test moving a file."""
        command = "把E盘的'report.docx'移到D盘"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.MOVE)
    
    # Test SEARCH operations
    def test_search_file(self):
        """Test searching for files."""
        command = "帮我在E盘查找是否有名称包含'测试'的文件"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.SEARCH)
        self.assertIsNotNone(result.source_name)
        self.assertIsNotNone(result.source_path)
    
    def test_search_folder(self):
        """Test searching for folders."""
        command = "在D盘搜索'2024'相关的文件"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.SEARCH)
    
    # Test RENAME operations
    def test_rename_file(self):
        """Test renaming a file."""
        command = "帮我把D盘的'oldname'改成'newname'"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.RENAME)
        self.assertIsNotNone(result.source_name)
        self.assertIsNotNone(result.target_name)
    
    def test_rename_folder(self):
        """Test renaming a folder."""
        command = "把E盘的'项目'文件夹改成'完成的项目'"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.RENAME)
    
    # Test file type detection
    def test_detect_folder_type(self):
        """Test detecting folder type."""
        command = "创建一个'test'文件夹"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.file_type, FileType.FOLDER)
    
    def test_detect_file_type(self):
        """Test detecting file type."""
        command = "删除一个'test'文件"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.file_type, FileType.FILE)
    
    # Test confidence score
    def test_confidence_score(self):
        """Test confidence score calculation."""
        command = "帮我在D盘创建一个名称为'test'的文件夹"
        result = self.nlu.parse(command)
        
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
    
    # Test invalid commands
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        command = "我想吃饭"
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.UNKNOWN)
    
    def test_empty_command(self):
        """Test handling of empty commands."""
        command = ""
        result = self.nlu.parse(command)
        
        self.assertEqual(result.operation, OperationType.UNKNOWN)

if __name__ == '__main__':
    unittest.main()
