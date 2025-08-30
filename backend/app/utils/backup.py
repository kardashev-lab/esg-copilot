"""
Backup and data persistence utilities for production deployment
"""

import os
import shutil
import tarfile
import gzip
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import logging
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError
import schedule
import time
import threading

logger = logging.getLogger(__name__)


@dataclass
class BackupConfig:
    """Backup configuration settings"""
    enabled: bool = True
    schedule: str = "0 2 * * *"  # Daily at 2 AM
    retention_days: int = 30
    backup_dir: str = "./backups"
    compress: bool = True
    
    # S3 configuration for cloud backups
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    
    # What to backup
    include_uploads: bool = True
    include_chroma_db: bool = True
    include_logs: bool = True
    include_config: bool = True


class BackupManager:
    """Manages automated backups of application data"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.backup_dir = Path(config.backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize S3 client if configured
        self.s3_client = None
        if config.s3_bucket and config.s3_access_key:
            try:
                self.s3_client = boto3.client(
                    's3',
                    region_name=config.s3_region,
                    aws_access_key_id=config.s3_access_key,
                    aws_secret_access_key=config.s3_secret_key
                )
                logger.info("S3 backup client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
    
    async def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a complete backup of application data"""
        
        if not self.config.enabled:
            raise ValueError("Backup is disabled in configuration")
        
        # Generate backup name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"esg_copilot_backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        backup_manifest = {
            "backup_name": backup_name,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0",
            "components": {},
            "status": "in_progress"
        }
        
        try:
            logger.info(f"Starting backup: {backup_name}")
            
            # Backup uploads directory
            if self.config.include_uploads:
                await self._backup_uploads(backup_path, backup_manifest)
            
            # Backup ChromaDB
            if self.config.include_chroma_db:
                await self._backup_chroma_db(backup_path, backup_manifest)
            
            # Backup logs
            if self.config.include_logs:
                await self._backup_logs(backup_path, backup_manifest)
            
            # Backup configuration
            if self.config.include_config:
                await self._backup_config(backup_path, backup_manifest)
            
            # Create manifest file
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                backup_manifest["status"] = "completed"
                backup_manifest["completed_at"] = datetime.utcnow().isoformat()
                json.dump(backup_manifest, f, indent=2)
            
            # Compress backup if enabled
            if self.config.compress:
                compressed_path = await self._compress_backup(backup_path)
                backup_manifest["compressed_size"] = os.path.getsize(compressed_path)
                
                # Remove uncompressed backup
                shutil.rmtree(backup_path)
                backup_path = compressed_path
            
            # Upload to S3 if configured
            if self.s3_client:
                await self._upload_to_s3(backup_path, backup_name)
            
            # Cleanup old backups
            await self._cleanup_old_backups()
            
            logger.info(f"Backup completed successfully: {backup_name}")
            return {
                "success": True,
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "manifest": backup_manifest
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            backup_manifest["status"] = "failed"
            backup_manifest["error"] = str(e)
            
            # Try to save manifest even if backup failed
            try:
                manifest_path = backup_path / "backup_manifest.json"
                with open(manifest_path, 'w') as f:
                    json.dump(backup_manifest, f, indent=2)
            except Exception:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "backup_name": backup_name,
                "manifest": backup_manifest
            }
    
    async def _backup_uploads(self, backup_path: Path, manifest: Dict[str, Any]):
        """Backup uploads directory"""
        from app.core.config import settings
        
        uploads_dir = Path(settings.upload_dir)
        if not uploads_dir.exists():
            logger.info("Uploads directory doesn't exist, skipping")
            return
        
        backup_uploads_dir = backup_path / "uploads"
        
        def copy_uploads():
            shutil.copytree(uploads_dir, backup_uploads_dir)
        
        await asyncio.to_thread(copy_uploads)
        
        # Calculate statistics
        total_files = sum(1 for _ in backup_uploads_dir.rglob("*") if _.is_file())
        total_size = sum(f.stat().st_size for f in backup_uploads_dir.rglob("*") if f.is_file())
        
        manifest["components"]["uploads"] = {
            "status": "completed",
            "total_files": total_files,
            "total_size_bytes": total_size,
            "path": "uploads/"
        }
        
        logger.info(f"Backed up {total_files} files from uploads directory")
    
    async def _backup_chroma_db(self, backup_path: Path, manifest: Dict[str, Any]):
        """Backup ChromaDB"""
        from app.core.config import settings
        
        chroma_dir = Path(settings.chroma_db_path)
        if not chroma_dir.exists():
            logger.info("ChromaDB directory doesn't exist, skipping")
            return
        
        backup_chroma_dir = backup_path / "chroma_db"
        
        def copy_chroma():
            shutil.copytree(chroma_dir, backup_chroma_dir)
        
        await asyncio.to_thread(copy_chroma)
        
        # Calculate statistics
        total_files = sum(1 for _ in backup_chroma_dir.rglob("*") if _.is_file())
        total_size = sum(f.stat().st_size for f in backup_chroma_dir.rglob("*") if f.is_file())
        
        manifest["components"]["chroma_db"] = {
            "status": "completed",
            "total_files": total_files,
            "total_size_bytes": total_size,
            "path": "chroma_db/"
        }
        
        logger.info(f"Backed up ChromaDB with {total_files} files")
    
    async def _backup_logs(self, backup_path: Path, manifest: Dict[str, Any]):
        """Backup log files"""
        logs_dir = Path("./logs")
        if not logs_dir.exists():
            logger.info("Logs directory doesn't exist, skipping")
            return
        
        backup_logs_dir = backup_path / "logs"
        backup_logs_dir.mkdir(exist_ok=True)
        
        # Only backup recent log files (last 7 days)
        cutoff_time = datetime.now() - timedelta(days=7)
        
        copied_files = 0
        total_size = 0
        
        for log_file in logs_dir.glob("*.log*"):
            if log_file.stat().st_mtime > cutoff_time.timestamp():
                shutil.copy2(log_file, backup_logs_dir)
                copied_files += 1
                total_size += log_file.stat().st_size
        
        manifest["components"]["logs"] = {
            "status": "completed",
            "total_files": copied_files,
            "total_size_bytes": total_size,
            "path": "logs/"
        }
        
        logger.info(f"Backed up {copied_files} log files")
    
    async def _backup_config(self, backup_path: Path, manifest: Dict[str, Any]):
        """Backup configuration files"""
        config_dir = backup_path / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Backup environment files (without sensitive data)
        env_files = [".env.example", "docker-compose.yml", "requirements.txt"]
        
        copied_files = 0
        for env_file in env_files:
            if os.path.exists(env_file):
                shutil.copy2(env_file, config_dir)
                copied_files += 1
        
        # Create system info file
        system_info = {
            "backup_time": datetime.utcnow().isoformat(),
            "python_version": os.sys.version,
            "platform": os.sys.platform,
            "environment_variables": {
                k: v for k, v in os.environ.items() 
                if not any(sensitive in k.lower() for sensitive in ["key", "password", "secret", "token"])
            }
        }
        
        with open(config_dir / "system_info.json", 'w') as f:
            json.dump(system_info, f, indent=2)
        
        manifest["components"]["config"] = {
            "status": "completed",
            "total_files": copied_files + 1,
            "path": "config/"
        }
        
        logger.info(f"Backed up {copied_files + 1} configuration files")
    
    async def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup directory"""
        compressed_path = backup_path.with_suffix('.tar.gz')
        
        def compress():
            with tarfile.open(compressed_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_path.name)
        
        await asyncio.to_thread(compress)
        
        original_size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
        compressed_size = compressed_path.stat().st_size
        compression_ratio = compressed_size / original_size if original_size > 0 else 1
        
        logger.info(f"Compressed backup: {original_size:,} -> {compressed_size:,} bytes ({compression_ratio:.2%})")
        
        return compressed_path
    
    async def _upload_to_s3(self, backup_path: Path, backup_name: str):
        """Upload backup to S3"""
        if not self.s3_client:
            return
        
        s3_key = f"backups/{backup_name}/{backup_path.name}"
        
        try:
            def upload():
                self.s3_client.upload_file(
                    str(backup_path),
                    self.config.s3_bucket,
                    s3_key
                )
            
            await asyncio.to_thread(upload)
            logger.info(f"Uploaded backup to S3: s3://{self.config.s3_bucket}/{s3_key}")
            
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
    
    async def _cleanup_old_backups(self):
        """Remove old backup files based on retention policy"""
        cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
        
        deleted_count = 0
        for backup_file in self.backup_dir.glob("esg_copilot_backup_*"):
            if backup_file.stat().st_mtime < cutoff_time.timestamp():
                if backup_file.is_dir():
                    shutil.rmtree(backup_file)
                else:
                    backup_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backup files")
        
        # Also cleanup S3 old backups if configured
        if self.s3_client:
            await self._cleanup_s3_backups()
    
    async def _cleanup_s3_backups(self):
        """Remove old S3 backup files"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
            
            def list_and_delete():
                response = self.s3_client.list_objects_v2(
                    Bucket=self.config.s3_bucket,
                    Prefix="backups/"
                )
                
                deleted_count = 0
                for obj in response.get('Contents', []):
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_time:
                        self.s3_client.delete_object(
                            Bucket=self.config.s3_bucket,
                            Key=obj['Key']
                        )
                        deleted_count += 1
                
                return deleted_count
            
            deleted_count = await asyncio.to_thread(list_and_delete)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old S3 backup files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup S3 backups: {e}")
    
    async def restore_backup(self, backup_name: str, restore_path: Optional[str] = None) -> Dict[str, Any]:
        """Restore from a backup"""
        
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        if not backup_file.exists():
            backup_file = self.backup_dir / backup_name
            if not backup_file.exists():
                return {"success": False, "error": f"Backup {backup_name} not found"}
        
        restore_path = restore_path or "./restore"
        restore_dir = Path(restore_path)
        restore_dir.mkdir(exist_ok=True)
        
        try:
            # Extract backup
            if backup_file.suffix == '.gz':
                with tarfile.open(backup_file, 'r:gz') as tar:
                    tar.extractall(restore_dir)
            else:
                shutil.copytree(backup_file, restore_dir / backup_name)
            
            # Read manifest
            manifest_path = restore_dir / backup_name / "backup_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            else:
                manifest = {"status": "unknown"}
            
            logger.info(f"Backup restored successfully to {restore_path}")
            
            return {
                "success": True,
                "restore_path": str(restore_dir),
                "manifest": manifest
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("esg_copilot_backup_*"):
            backup_info = {
                "name": backup_file.stem,
                "path": str(backup_file),
                "size_bytes": backup_file.stat().st_size if backup_file.is_file() else self._get_dir_size(backup_file),
                "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                "type": "compressed" if backup_file.suffix == ".gz" else "directory"
            }
            
            # Try to read manifest if available
            manifest_path = backup_file / "backup_manifest.json" if backup_file.is_dir() else None
            if manifest_path and manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        backup_info["manifest"] = manifest
                except Exception:
                    pass
            
            backups.append(backup_info)
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def _get_dir_size(self, directory: Path) -> int:
        """Calculate total size of directory"""
        return sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())


# Backup scheduler
class BackupScheduler:
    """Handles scheduled backup operations"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.scheduler_thread = None
        self.running = False
    
    def start(self):
        """Start the backup scheduler"""
        if self.running:
            return
        
        self.running = True
        
        # Schedule backup based on configuration
        schedule.every().day.at("02:00").do(self._run_scheduled_backup)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Backup scheduler started")
    
    def stop(self):
        """Stop the backup scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Backup scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _run_scheduled_backup(self):
        """Run a scheduled backup"""
        logger.info("Running scheduled backup")
        
        # Run backup in async context
        import asyncio
        
        async def run_backup():
            try:
                result = await self.backup_manager.create_backup()
                if result["success"]:
                    logger.info(f"Scheduled backup completed: {result['backup_name']}")
                else:
                    logger.error(f"Scheduled backup failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Scheduled backup error: {e}")
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_backup())
        loop.close()


# Global backup manager
backup_manager: Optional[BackupManager] = None
backup_scheduler: Optional[BackupScheduler] = None


def initialize_backup_system(config: BackupConfig):
    """Initialize the backup system"""
    global backup_manager, backup_scheduler
    
    backup_manager = BackupManager(config)
    
    if config.enabled:
        backup_scheduler = BackupScheduler(backup_manager)
        backup_scheduler.start()
        logger.info("Backup system initialized and scheduled")
    else:
        logger.info("Backup system initialized but disabled")


def shutdown_backup_system():
    """Shutdown the backup system"""
    global backup_scheduler
    
    if backup_scheduler:
        backup_scheduler.stop()
        backup_scheduler = None
    
    logger.info("Backup system shutdown")
