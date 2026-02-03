"""
Audit Logger for maintaining confidentiality and audit trails
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
import hashlib


class AuditLogger:
    """
    JSON-based audit logging system for contract analysis operations.
    """
    
    def __init__(self, logs_dir: str = "logs"):
        """
        Initialize the audit logger.
        
        Args:
            logs_dir: Directory to store audit logs
        """
        self.logs_dir = logs_dir
        self._ensure_logs_directory()
    
    def _ensure_logs_directory(self):
        """Create logs directory if it doesn't exist."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
    
    def _get_log_file_path(self) -> str:
        """Get the current log file path (daily rotation)."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.logs_dir, f"audit_{date_str}.json")
    
    def _generate_document_hash(self, content: str) -> str:
        """Generate a hash for document content (for confidentiality)."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def log_operation(self, 
                      operation: str,
                      document_name: str,
                      document_hash: Optional[str] = None,
                      details: Optional[Dict[str, Any]] = None,
                      session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Log an audit operation.
        
        Args:
            operation: Type of operation (upload, analyze, export, etc.)
            document_name: Name of the document (filename)
            document_hash: Hash of document content (for identification)
            details: Additional operation details
            session_id: User session identifier
            
        Returns:
            The logged entry
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "document_name": document_name,
            "document_hash": document_hash,
            "session_id": session_id,
            "details": details or {}
        }
        
        self._write_log_entry(entry)
        return entry
    
    def log_upload(self, 
                   filename: str, 
                   file_size: int, 
                   file_type: str,
                   content_hash: str,
                   session_id: Optional[str] = None) -> Dict[str, Any]:
        """Log a document upload operation."""
        return self.log_operation(
            operation="DOCUMENT_UPLOAD",
            document_name=filename,
            document_hash=content_hash,
            details={
                "file_size_bytes": file_size,
                "file_type": file_type
            },
            session_id=session_id
        )
    
    def log_analysis(self,
                     filename: str,
                     content_hash: str,
                     analysis_type: str,
                     contract_type: Optional[str] = None,
                     risk_score: Optional[float] = None,
                     session_id: Optional[str] = None) -> Dict[str, Any]:
        """Log a contract analysis operation."""
        return self.log_operation(
            operation="CONTRACT_ANALYSIS",
            document_name=filename,
            document_hash=content_hash,
            details={
                "analysis_type": analysis_type,
                "contract_type": contract_type,
                "risk_score": risk_score
            },
            session_id=session_id
        )
    
    def log_export(self,
                   filename: str,
                   content_hash: str,
                   export_format: str,
                   export_path: str,
                   session_id: Optional[str] = None) -> Dict[str, Any]:
        """Log a document export operation."""
        return self.log_operation(
            operation="DOCUMENT_EXPORT",
            document_name=filename,
            document_hash=content_hash,
            details={
                "export_format": export_format,
                "export_path": export_path
            },
            session_id=session_id
        )
    
    def log_llm_query(self,
                      filename: str,
                      content_hash: str,
                      query_type: str,
                      tokens_used: Optional[int] = None,
                      session_id: Optional[str] = None) -> Dict[str, Any]:
        """Log an LLM query operation."""
        return self.log_operation(
            operation="LLM_QUERY",
            document_name=filename,
            document_hash=content_hash,
            details={
                "query_type": query_type,
                "tokens_used": tokens_used
            },
            session_id=session_id
        )
    
    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write a log entry to the log file."""
        log_file = self._get_log_file_path()
        
        # Read existing logs
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
        
        # Append new entry
        logs.append(entry)
        
        # Write back
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def get_logs(self, 
                 date: Optional[str] = None,
                 operation: Optional[str] = None,
                 document_hash: Optional[str] = None) -> list:
        """
        Retrieve audit logs with optional filtering.
        
        Args:
            date: Filter by date (YYYY-MM-DD)
            operation: Filter by operation type
            document_hash: Filter by document hash
            
        Returns:
            List of matching log entries
        """
        if date:
            log_file = os.path.join(self.logs_dir, f"audit_{date}.json")
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            # Get all logs
            logs = []
            for filename in os.listdir(self.logs_dir):
                if filename.startswith("audit_") and filename.endswith(".json"):
                    filepath = os.path.join(self.logs_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        logs.extend(json.load(f))
        
        # Apply filters
        if operation:
            logs = [l for l in logs if l.get("operation") == operation]
        if document_hash:
            logs = [l for l in logs if l.get("document_hash") == document_hash]
        
        return logs
    
    def generate_document_id(self, content: str) -> str:
        """Generate a unique document identifier from content."""
        return self._generate_document_hash(content)


# Global logger instance
_logger: Optional[AuditLogger] = None


def get_audit_logger(logs_dir: str = "logs") -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _logger
    if _logger is None:
        _logger = AuditLogger(logs_dir)
    return _logger
