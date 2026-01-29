"""
Job Manager for handling job persistence in SQLite database
Manages job lifecycle: creation, updates, status tracking, and cleanup
"""
from datetime import datetime, timedelta
import sqlite3
import json
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any


class JobManager:
    """Manages job persistence in SQLite database"""
    
    def __init__(self, db_path: Optional[str] = None, retention_days: int = 7):
        """
        Initialize JobManager with database path and retention policy
        
        Args:
            db_path: Path to SQLite database file (default: database/jobs.db)
            retention_days: Number of days to retain completed jobs (default: 7)
        """
        if db_path is None:
            # Default to database/jobs.db in backend folder
            db_dir = Path(__file__).parent
            db_path = db_dir / 'jobs.db'
        
        self.db_path = Path(db_path)
        self.retention_days = retention_days
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database with schema if not exists"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    message TEXT,
                    error TEXT,
                    
                    -- File information
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    output_file TEXT,
                    output_path TEXT,
                    component TEXT DEFAULT 'upload',
                    
                    -- File metadata
                    file_size INTEGER,
                    file_rows INTEGER,
                    file_columns INTEGER,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    
                    -- Optional features
                    callback_url TEXT,
                    email TEXT,
                    
                    -- API tracking
                    api_key TEXT,
                    user_ip TEXT,
                    
                    -- Processing details (JSON)
                    steps_json TEXT,
                    logs_json TEXT,
                    file_info_json TEXT
                )
            ''')
            
            # Create indexes for common queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON jobs(expires_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_updated_at ON jobs(updated_at DESC)')
            
            # Migrate existing data: Add component column if it doesn't exist
            try:
                # Check if component column exists
                cursor = conn.execute("PRAGMA table_info(jobs)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'component' not in columns:
                    print("🔄 Migrating database: adding component column...")
                    conn.execute("ALTER TABLE jobs ADD COLUMN component TEXT DEFAULT 'upload'")
                    conn.commit()
                    print("✅ Migration complete: component column added")
            except Exception as e:
                print(f"⚠️  Migration note: {e}")
            
            conn.commit()
            print(f"✅ Database initialized at: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency (reads don't block writes)
        conn.execute('PRAGMA journal_mode=WAL')
        # Optimize for speed
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA cache_size=10000')
        try:
            yield conn
        finally:
            conn.close()
    
    def create_job(self, job_id: str, filename: str, original_filename: str, **kwargs) -> bool:
        """
        Create a new job in the database
        
        Args:
            job_id: Unique job identifier
            filename: Stored filename (with timestamp)
            original_filename: Original uploaded filename
            **kwargs: Additional job parameters (callback_url, email, steps, logs, etc.)
        
        Returns:
            bool: True if created successfully
        """
        try:
            with self._get_connection() as conn:
                # Prepare steps and logs as JSON
                steps_json = json.dumps(kwargs.get('steps', []))
                logs_json = json.dumps(kwargs.get('logs', []))
                file_info_json = json.dumps(kwargs.get('file_info', {}))
                
                conn.execute('''
                    INSERT INTO jobs (
                        job_id, status, filename, original_filename, component,
                        steps_json, logs_json, file_info_json,
                        callback_url, email, api_key, user_ip,
                        file_size, file_rows, file_columns, progress, message
                    )
                    VALUES (?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id,
                    filename,
                    original_filename,
                    kwargs.get('component', 'upload'),
                    steps_json,
                    logs_json,
                    file_info_json,
                    kwargs.get('callback_url'),
                    kwargs.get('email'),
                    kwargs.get('api_key'),
                    kwargs.get('user_ip'),
                    kwargs.get('file_size'),
                    kwargs.get('file_rows'),
                    kwargs.get('file_columns'),
                    kwargs.get('progress', 0),
                    kwargs.get('message', 'Job queued')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Failed to create job {job_id}: {e}")
            return False
    
    def update_job(self, job_id: str, **fields) -> bool:
        """
        Update job fields dynamically
        
        Args:
            job_id: Job identifier
            **fields: Fields to update (status, progress, message, error, etc.)
        
        Returns:
            bool: True if updated successfully
        """
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Build dynamic UPDATE query
                set_clauses = []
                values = []
                
                for key, value in fields.items():
                    # Handle JSON fields
                    if key in ['steps', 'logs', 'file_info']:
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                            key = f"{key}_json"
                        else:
                            key = f"{key}_json"
                    
                    # Handle logs - append instead of replace
                    if key == 'logs_json' and isinstance(fields.get('logs'), list):
                        # Get existing logs and append
                        existing_job = self.get_job(job_id)
                        if existing_job:
                            existing_logs = existing_job.get('logs', [])
                            existing_logs.extend(fields['logs'])
                            value = json.dumps(existing_logs)
                    
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                if not set_clauses:
                    return False
                
                # Always update updated_at timestamp
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                
                # Set expires_at when job completes (if not already set)
                if fields.get('status') == 'completed' and 'expires_at' not in fields:
                    expires_at = datetime.utcnow() + timedelta(days=self.retention_days)
                    set_clauses.append("expires_at = ?")
                    values.append(expires_at.isoformat())
                
                # Set finished_at when job completes or fails
                if fields.get('status') in ['completed', 'failed', 'error'] and 'finished_at' not in fields:
                    set_clauses.append("finished_at = CURRENT_TIMESTAMP")
                
                # Set started_at when job starts processing (if not already set)
                if fields.get('status') == 'processing':
                    # Check if started_at is already set
                    existing = self.get_job(job_id)
                    if existing and not existing.get('started_at'):
                        set_clauses.append("started_at = CURRENT_TIMESTAMP")
                
                values.append(job_id)
                query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE job_id = ?"
                
                with self._get_connection() as conn:
                    cursor = conn.execute(query, values)
                    conn.commit()
                    return cursor.rowcount > 0
                    
            except sqlite3.OperationalError as e:
                if 'locked' in str(e).lower() and attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                print(f"❌ Failed to update job {job_id} after retries: {e}")
                return False
            except Exception as e:
                print(f"❌ Failed to update job {job_id}: {e}")
                return False
        
        return False
    
    def add_log(self, job_id: str, message: str, progress: Optional[int] = None) -> bool:
        """
        Add a log entry to a job
        
        Args:
            job_id: Job identifier
            message: Log message
            progress: Optional progress percentage
        
        Returns:
            bool: True if log added successfully
        """
        job = self.get_job(job_id)
        if not job:
            return False
        
        logs = job.get('logs', [])
        logs.append({
            'ts': datetime.utcnow().isoformat() + 'Z',
            'message': message,
            'progress': progress
        })
        
        return self.update_job(job_id, logs=logs)
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID
        
        Args:
            job_id: Job identifier
        
        Returns:
            Dict with job data or None if not found
        """
        try:
            with self._get_connection() as conn:
                row = conn.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,)).fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
        except Exception as e:
            print(f"❌ Failed to get job {job_id}: {e}")
            return None
    
    def get_jobs(self, status: Optional[str] = None, limit: int = 50, offset: int = 0, 
                 order_by: str = 'updated_at', order_desc: bool = True) -> List[Dict[str, Any]]:
        """
        Get jobs with optional filtering and pagination
        
        Args:
            status: Filter by status (None = all)
            limit: Maximum number of jobs to return (default: 50 for better performance)
            offset: Number of jobs to skip
            order_by: Field to order by (default: updated_at for better index usage)
            order_desc: Order descending if True
        
        Returns:
            List of job dictionaries
        """
        try:
            order_dir = 'DESC' if order_desc else 'ASC'
            with self._get_connection() as conn:
                if status:
                    query = f'SELECT * FROM jobs WHERE status = ? ORDER BY {order_by} {order_dir} LIMIT ? OFFSET ?'
                    rows = conn.execute(query, (status, limit, offset)).fetchall()
                else:
                    query = f'SELECT * FROM jobs ORDER BY {order_by} {order_dir} LIMIT ? OFFSET ?'
                    rows = conn.execute(query, (limit, offset)).fetchall()
                
                return [self._row_to_dict(row) for row in rows]
        except sqlite3.OperationalError as e:
            if 'locked' in str(e).lower():
                print(f"⚠️  Database locked, retrying...")
                # Quick retry for lock errors
                import time
                time.sleep(0.1)
                return self.get_jobs(status, limit, offset, order_by, order_desc)
            print(f"❌ Failed to get jobs: {e}")
            return []
        except Exception as e:
            print(f"❌ Failed to get jobs: {e}")
            return []
    
    def get_recent_jobs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most recent jobs (for dashboard/panel display)
        
        Args:
            limit: Number of recent jobs to return
        
        Returns:
            List of recent job dictionaries
        """
        return self.get_jobs(limit=limit, order_by='updated_at', order_desc=True)
    
    def delete_job(self, job_id: str, delete_files: bool = True) -> bool:
        """
        Delete job from database and optionally delete associated files
        
        Args:
            job_id: Job identifier
            delete_files: If True, delete associated output files
        
        Returns:
            bool: True if deleted successfully
        """
        try:
            job = self.get_job(job_id)
            if not job:
                return False
            
            # Delete associated files if requested
            if delete_files:
                self._delete_job_files(job)
            
            # Delete from database
            with self._get_connection() as conn:
                conn.execute('DELETE FROM jobs WHERE job_id = ?', (job_id,))
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Failed to delete job {job_id}: {e}")
            return False
    
    def get_expired_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all jobs past their expiration date
        
        Returns:
            List of expired job dictionaries
        """
        try:
            with self._get_connection() as conn:
                now = datetime.utcnow().isoformat()
                rows = conn.execute(
                    'SELECT * FROM jobs WHERE expires_at IS NOT NULL AND expires_at < ?',
                    (now,)
                ).fetchall()
                return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Failed to get expired jobs: {e}")
            return []
    
    def cleanup_expired_jobs(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Delete expired jobs and their associated files
        
        Args:
            dry_run: If True, don't actually delete, just return what would be deleted
        
        Returns:
            Dict with cleanup statistics
        """
        expired = self.get_expired_jobs()
        deleted_count = 0
        deleted_jobs = []
        errors = []
        
        for job in expired:
            job_id = job['job_id']
            
            if dry_run:
                deleted_jobs.append(job_id)
                continue
            
            try:
                # Delete files
                self._delete_job_files(job)
                
                # Delete job record
                if self.delete_job(job_id, delete_files=False):  # Files already deleted above
                    deleted_count += 1
                    deleted_jobs.append(job_id)
                    
            except Exception as e:
                errors.append({'job_id': job_id, 'error': str(e)})
        
        return {
            'deleted_count': deleted_count,
            'deleted_jobs': deleted_jobs,
            'errors': errors,
            'dry_run': dry_run
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dict with job statistics
        """
        try:
            with self._get_connection() as conn:
                total = conn.execute('SELECT COUNT(*) as count FROM jobs').fetchone()['count']
                queued = conn.execute('SELECT COUNT(*) as count FROM jobs WHERE status = "queued"').fetchone()['count']
                processing = conn.execute('SELECT COUNT(*) as count FROM jobs WHERE status = "processing"').fetchone()['count']
                completed = conn.execute('SELECT COUNT(*) as count FROM jobs WHERE status = "completed"').fetchone()['count']
                failed = conn.execute('SELECT COUNT(*) as count FROM jobs WHERE status IN ("failed", "error")').fetchone()['count']
                
                return {
                    'total_jobs': total,
                    'queued': queued,
                    'processing': processing,
                    'completed': completed,
                    'failed': failed,
                    'database_path': str(self.db_path),
                    'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {}
    
    def _delete_job_files(self, job: Dict[str, Any]):
        """Delete files associated with a job"""
        # Delete output file
        if job.get('output_path') and os.path.exists(job['output_path']):
            try:
                os.remove(job['output_path'])
                print(f"🗑️ Deleted output file: {job['output_path']}")
            except Exception as e:
                print(f"⚠️ Failed to delete output file {job['output_path']}: {e}")
        
        # Try to delete input file (if it still exists in inbound)
        if job.get('filename'):
            # Construct inbound path
            inbound_path = Path(__file__).parent.parent / 'inbound' / job['filename']
            if inbound_path.exists():
                try:
                    os.remove(str(inbound_path))
                    print(f"🗑️ Deleted inbound file: {inbound_path}")
                except Exception as e:
                    print(f"⚠️ Failed to delete inbound file {inbound_path}: {e}")
    
    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary with JSON parsing"""
        d = dict(row)
        
        # Parse JSON fields
        if d.get('steps_json'):
            try:
                d['steps'] = json.loads(d['steps_json'])
            except:
                d['steps'] = []
        
        if d.get('logs_json'):
            try:
                d['logs'] = json.loads(d['logs_json'])
            except:
                d['logs'] = []
        
        if d.get('file_info_json'):
            try:
                d['file_info'] = json.loads(d['file_info_json'])
            except:
                d['file_info'] = {}
        
        return d


# Global instance - initialized with environment variable or default
def get_retention_days() -> int:
    """Get retention days from environment or use default"""
    try:
        return int(os.getenv('JOB_RETENTION_DAYS', '7'))
    except:
        return 7


# Initialize global job_manager instance
job_manager = JobManager(retention_days=get_retention_days())
