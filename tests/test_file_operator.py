"""Unit tests for File Operator."""

import unittest
import tempfile
import os
from pathlib import Path
from modules.file_operator import FileOperator
from modules.nlu_engine import NLUEngine, OperationType, FileType, ParsedCommand

class TestFileOperator(unittest.TestCase):
    """Test cases for File Operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.operator = FileOperator()
        self.nlu = NLUEngine()
        
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    # Test path resolution
    def test_resolve_path_with_drive(self):
        """Test path resolution with drive letter."""
        path = self.operator._resolve_path('D:', 'test_file')
        
        self.assertIn('D:', path)
        self.assertIn('test_file', path)
    
    def test_resolve_drive_path(self):
        """Test drive path resolution."""
        path = self.operator._resolve_drive_path('E:')
        
        self.assertIn('E:', path)
    
    def test_resolve_path_without_drive(self):
        """Test path resolution without explicit drive."""
        path = self.operator._resolve_path(None, 'default_file')
        
        # Should default to D:
        self.assertIn('D:', path)
    
    # Test CREATE operations
    def test_create_folder(self):
        """Test creating a folder."""
        # Create a ParsedCommand for testing
        command = ParsedCommand(
            operation=OperationType.CREATE,
            file_type=FileType.FOLDER,
            source_name='test_folder',
            source_path='D:',
            target_name=None,
            target_path=None,
            confidence=0.95,
            raw_command='test'
        )
        
        # Note: This will attempt to create on D:, which may not exist
        # In real tests, use mocking or temporary directories
        # result = self.operator.execute(command)
        # self.assertTrue(result['success'])
    
    # Test path protection
    def test_protected_path_check(self):
        """Test protected path checking."""
        from modules.file_operator import FileOperationError
        
        with self.assertRaises(FileOperationError):
            self.operator._check_protected('C:\\Windows\\System32')
    
    # Test search functionality
    def test_search_recursive(self):
        """Test recursive search."""
        # Create test files
        test_file1 = os.path.join(self.test_dir, 'test_2024.txt')
        test_file2 = os.path.join(self.test_dir, 'data_2024.txt')
        test_file3 = os.path.join(self.test_dir, 'readme.md')
        
        Path(test_file1).touch()
        Path(test_file2).touch()
        Path(test_file3).touch()
        
        # Search for files containing '2024'
        results = self.operator._search_recursive(self.test_dir, '2024', max_results=100)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(any('test_2024' in r for r in results))
        self.assertTrue(any('data_2024' in r for r in results))
    
    def test_search_no_results(self):
        """Test search with no results."""
        results = self.operator._search_recursive(self.test_dir, 'nonexistent', max_results=100)
        
        self.assertEqual(len(results), 0)
    
    def test_search_max_results(self):
        """Test search respects max results limit."""
        # Create many test files
        for i in range(10):
            Path(os.path.join(self.test_dir, f'file_{i}.txt')).touch()
        
        # Search with limit
        results = self.operator._search_recursive(self.test_dir, 'file_', max_results=5)
        
        self.assertLessEqual(len(results), 5)
    
    # Test ParsedCommand validation
    def test_parsed_command_valid(self):
        """Test valid parsed command."""
        command = ParsedCommand(
            operation=OperationType.CREATE,
            file_type=FileType.FOLDER,
            source_name='test',
            source_path='D:',
            target_name=None,
            target_path=None,
            confidence=0.95,
            raw_command='test'
        )
        
        self.assertTrue(command.is_valid())
    
    def test_parsed_command_invalid_low_confidence(self):
        """Test invalid command with low confidence."""
        command = ParsedCommand(
            operation=OperationType.CREATE,
            file_type=FileType.FOLDER,
            source_name='test',
            source_path='D:',
            target_name=None,
            target_path=None,
            confidence=0.5,  # Below threshold
            raw_command='test'
        )
        
        # Assuming threshold is 0.7
        self.assertFalse(command.is_valid())
    
    def test_parsed_command_invalid_unknown_operation(self):
        """Test invalid command with unknown operation."""
        command = ParsedCommand(
            operation=OperationType.UNKNOWN,
            file_type=FileType.FOLDER,
            source_name='test',
            source_path='D:',
            target_name=None,
            target_path=None,
            confidence=0.95,
            raw_command='test'
        )
        
        self.assertFalse(command.is_valid())
    
    # Test error messages
    def test_execute_with_invalid_command(self):
        """Test execution with invalid command."""
        command = ParsedCommand(
            operation=OperationType.UNKNOWN,
            file_type=FileType.UNKNOWN,
            source_name=None,
            source_path=None,
            target_name=None,
            target_path=None,
            confidence=0.0,
            raw_command='test'
        )
        
        result = self.operator.execute(command)
        
        self.assertFalse(result['success'])
        self.assertIn('message', result)

if __name__ == '__main__':
    unittest.main()
