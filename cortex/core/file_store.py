"""
File-based memory store for Cortex SDK.
Manages file storage and retrieval with metadata tracking.
"""

import os
import hashlib
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
from cortex.utils.schema import FileMemory
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


class FileStore:
    """
    File storage system for managing documents and files with metadata.
    """
    
    def __init__(self, storage_path: str = "./cortex_files", capacity: int = 1000):
        """
        Initialize file store.
        
        Args:
            storage_path: Path to file storage directory
            capacity: Maximum number of files to store
        """
        self.storage_path = Path(storage_path)
        self.capacity = capacity
        self.files: Dict[str, FileMemory] = {}
        self.logger = get_logger(__name__)
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Initialized FileStore at {self.storage_path} with capacity: {capacity}")
    
    def _generate_file_id(self, file_path: str) -> str:
        """
        Generate unique file ID based on path and timestamp.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Unique file ID
        """
        content = f"{file_path}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_file_info(self, file_path: str) -> Dict:
        """
        Get file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file info
        """
        path = Path(file_path)
        
        return {
            'name': path.name,
            'type': path.suffix.lstrip('.') or 'unknown',
            'size': path.stat().st_size if path.exists() else 0,
        }
    
    def add(
        self,
        file_path: str,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        copy_file: bool = True,
        content_summary: Optional[str] = None
    ) -> Optional[str]:
        """
        Add a file to the store.
        
        Args:
            file_path: Path to the file
            metadata: Additional metadata
            tags: File tags
            copy_file: Whether to copy file to storage
            content_summary: Summary of file content
            
        Returns:
            File ID or None if failed
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File does not exist: {file_path}")
                return None
            
            # Check capacity
            if len(self.files) >= self.capacity:
                self.logger.warning("File store at capacity")
                return None
            
            # Generate file ID
            file_id = self._generate_file_id(file_path)
            
            # Get file info
            file_info = self._get_file_info(file_path)
            
            # Determine storage path
            if copy_file:
                # Copy file to storage directory
                dest_path = self.storage_path / f"{file_id}_{file_info['name']}"
                import shutil
                shutil.copy2(file_path, dest_path)
                stored_path = str(dest_path)
            else:
                # Keep reference to original file
                stored_path = file_path
            
            # Create FileMemory object
            file_memory = FileMemory(
                id=file_id,
                file_path=stored_path,
                file_name=file_info['name'],
                file_type=file_info['type'],
                file_size=file_info['size'],
                content_summary=content_summary,
                metadata=metadata or {},
                tags=tags or []
            )
            
            # Store file memory
            self.files[file_id] = file_memory
            
            self.logger.info(f"Added file to store: {file_id} ({file_info['name']})")
            return file_id
            
        except Exception as e:
            self.logger.error(f"Failed to add file: {e}", exc_info=True)
            return None
    
    def get(self, file_id: str) -> Optional[FileMemory]:
        """
        Get file memory by ID.
        
        Args:
            file_id: File identifier
            
        Returns:
            FileMemory object or None
        """
        file_memory = self.files.get(file_id)
        
        if file_memory:
            self.logger.debug(f"Retrieved file from store: {file_id}")
        
        return file_memory
    
    def remove(self, file_id: str, delete_file: bool = False) -> bool:
        """
        Remove a file from store.
        
        Args:
            file_id: File identifier
            delete_file: Whether to delete the actual file
            
        Returns:
            True if removed successfully
        """
        if file_id not in self.files:
            return False
        
        file_memory = self.files[file_id]
        
        # Delete actual file if requested
        if delete_file:
            try:
                file_path = Path(file_memory.file_path)
                if file_path.exists():
                    file_path.unlink()
                    self.logger.debug(f"Deleted file: {file_memory.file_path}")
            except Exception as e:
                self.logger.error(f"Failed to delete file: {e}", exc_info=True)
        
        # Remove from store
        del self.files[file_id]
        self.logger.info(f"Removed file from store: {file_id}")
        return True
    
    def update(self, file_memory: FileMemory) -> bool:
        """
        Update file memory metadata.
        
        Args:
            file_memory: Updated FileMemory object
            
        Returns:
            True if updated successfully
        """
        if file_memory.id not in self.files:
            return False
        
        file_memory.updated_at = datetime.utcnow()
        self.files[file_memory.id] = file_memory
        
        self.logger.debug(f"Updated file in store: {file_memory.id}")
        return True
    
    def get_all(self) -> List[FileMemory]:
        """
        Get all file memories.
        
        Returns:
            List of all file memories
        """
        return list(self.files.values())
    
    def search(
        self,
        file_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[FileMemory]:
        """
        Search files by criteria.
        
        Args:
            file_type: Filter by file type
            tags: Filter by tags
            min_size: Minimum file size
            max_size: Maximum file size
            limit: Maximum results
            
        Returns:
            List of matching file memories
        """
        results = []
        
        for file_memory in self.files.values():
            # Filter by file type
            if file_type and file_memory.file_type != file_type:
                continue
            
            # Filter by tags
            if tags and not any(tag in file_memory.tags for tag in tags):
                continue
            
            # Filter by size
            if min_size and file_memory.file_size < min_size:
                continue
            if max_size and file_memory.file_size > max_size:
                continue
            
            results.append(file_memory)
            
            # Check limit
            if limit and len(results) >= limit:
                break
        
        return results
    
    def clear(self, delete_files: bool = False):
        """
        Clear all files from store.
        
        Args:
            delete_files: Whether to delete actual files
        """
        count = len(self.files)
        
        if delete_files:
            for file_memory in self.files.values():
                try:
                    file_path = Path(file_memory.file_path)
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    self.logger.error(f"Failed to delete file: {e}")
        
        self.files.clear()
        self.logger.info(f"Cleared {count} files from store")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the file store.
        
        Returns:
            Dictionary of statistics
        """
        files_list = list(self.files.values())
        
        stats = {
            'total_files': len(files_list),
            'capacity': self.capacity,
            'utilization': len(files_list) / self.capacity if self.capacity > 0 else 0,
        }
        
        if files_list:
            stats.update({
                'total_size_bytes': sum(f.file_size for f in files_list),
                'avg_size_bytes': sum(f.file_size for f in files_list) / len(files_list),
                'oldest_file': min(f.created_at for f in files_list),
                'newest_file': max(f.created_at for f in files_list),
            })
            
            # Count by file type
            type_counts = {}
            for f in files_list:
                type_counts[f.file_type] = type_counts.get(f.file_type, 0) + 1
            stats['file_types'] = type_counts
        
        return stats
    
    def is_full(self) -> bool:
        """Check if store is at capacity."""
        return len(self.files) >= self.capacity
    
    def get_by_type(self, file_type: str) -> List[FileMemory]:
        """
        Get all files of a specific type.
        
        Args:
            file_type: File type/extension
            
        Returns:
            List of file memories
        """
        return [f for f in self.files.values() if f.file_type == file_type]
    
    def get_by_tags(self, tags: List[str]) -> List[FileMemory]:
        """
        Get files with specific tags.
        
        Args:
            tags: List of tags
            
        Returns:
            List of file memories
        """
        return [f for f in self.files.values() if any(tag in f.tags for tag in tags)]

