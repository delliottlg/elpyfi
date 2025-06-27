#!/usr/bin/env python3
"""
Issue Tracker for PM Claude
Tracks issues, notes, and TODOs for services without diving into code
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Issue:
    """Represents an issue or note"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    service: str = ""
    title: str = ""
    description: str = ""
    status: IssueStatus = IssueStatus.OPEN
    severity: IssueSeverity = IssueSeverity.MEDIUM
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Issue':
        """Create from dictionary"""
        # Convert string enums back to enum types
        if 'status' in data:
            data['status'] = IssueStatus(data['status'])
        if 'severity' in data:
            data['severity'] = IssueSeverity(data['severity'])
        return cls(**data)


class IssueTracker:
    """Manages issues and notes for services"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.issues_file = base_path / "data" / "issues.json"
        self.issues_file.parent.mkdir(exist_ok=True)
        self.issues: Dict[str, Issue] = self._load_issues()
    
    def _load_issues(self) -> Dict[str, Issue]:
        """Load issues from file"""
        if not self.issues_file.exists():
            return {}
        
        try:
            with open(self.issues_file, 'r') as f:
                data = json.load(f)
                return {
                    id: Issue.from_dict(issue_data) 
                    for id, issue_data in data.items()
                }
        except Exception as e:
            print(f"Error loading issues: {e}")
            return {}
    
    def _save_issues(self):
        """Save issues to file"""
        data = {
            id: issue.to_dict() 
            for id, issue in self.issues.items()
        }
        
        with open(self.issues_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_issue(
        self, 
        service: str, 
        title: str, 
        description: str = "",
        severity: IssueSeverity = IssueSeverity.MEDIUM,
        tags: Optional[List[str]] = None
    ) -> Issue:
        """Add a new issue"""
        issue = Issue(
            service=service,
            title=title,
            description=description,
            severity=severity,
            tags=tags or []
        )
        
        self.issues[issue.id] = issue
        self._save_issues()
        
        return issue
    
    def update_issue(
        self, 
        issue_id: str,
        status: Optional[IssueStatus] = None,
        severity: Optional[IssueSeverity] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Issue]:
        """Update an existing issue"""
        if issue_id not in self.issues:
            return None
        
        issue = self.issues[issue_id]
        
        if status is not None:
            issue.status = status
        if severity is not None:
            issue.severity = severity
        if description is not None:
            issue.description = description
        if tags is not None:
            issue.tags = tags
        
        issue.updated_at = datetime.now().isoformat()
        self._save_issues()
        
        return issue
    
    def get_issues(
        self, 
        service: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        severity: Optional[IssueSeverity] = None
    ) -> List[Issue]:
        """Get filtered list of issues"""
        issues = list(self.issues.values())
        
        if service:
            issues = [i for i in issues if i.service == service]
        if status:
            issues = [i for i in issues if i.status == status]
        if severity:
            issues = [i for i in issues if i.severity == severity]
        
        # Sort by created date (newest first)
        issues.sort(key=lambda x: x.created_at, reverse=True)
        
        return issues
    
    def get_issue(self, issue_id: str) -> Optional[Issue]:
        """Get a specific issue"""
        return self.issues.get(issue_id)
    
    def resolve_issue(self, issue_id: str) -> Optional[Issue]:
        """Mark an issue as resolved"""
        return self.update_issue(issue_id, status=IssueStatus.RESOLVED)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get issue summary statistics"""
        all_issues = list(self.issues.values())
        
        summary = {
            "total": len(all_issues),
            "by_status": {},
            "by_severity": {},
            "by_service": {}
        }
        
        # Count by status
        for status in IssueStatus:
            count = sum(1 for i in all_issues if i.status == status)
            if count > 0:
                summary["by_status"][status.value] = count
        
        # Count by severity
        for severity in IssueSeverity:
            count = sum(1 for i in all_issues if i.severity == severity)
            if count > 0:
                summary["by_severity"][severity.value] = count
        
        # Count by service
        for issue in all_issues:
            if issue.service:
                summary["by_service"][issue.service] = \
                    summary["by_service"].get(issue.service, 0) + 1
        
        return summary
    
    def print_issues(self, issues: Optional[List[Issue]] = None):
        """Print formatted issue list"""
        if issues is None:
            issues = self.get_issues()
        
        if not issues:
            print("No issues found")
            return
        
        print(f"\n📋 Issues ({len(issues)} total)")
        print("=" * 80)
        
        for issue in issues:
            # Status icon
            status_icon = {
                IssueStatus.OPEN: "🔴",
                IssueStatus.IN_PROGRESS: "🟡",
                IssueStatus.RESOLVED: "🟢",
                IssueStatus.WONT_FIX: "⚪"
            }.get(issue.status, "❓")
            
            # Severity color
            severity_icon = {
                IssueSeverity.LOW: "🟦",
                IssueSeverity.MEDIUM: "🟨",
                IssueSeverity.HIGH: "🟧",
                IssueSeverity.CRITICAL: "🟥"
            }.get(issue.severity, "")
            
            print(f"\n{status_icon} [{issue.id}] {issue.title}")
            print(f"   Service: {issue.service} | Severity: {severity_icon} {issue.severity.value}")
            if issue.description:
                print(f"   {issue.description}")
            if issue.tags:
                print(f"   Tags: {', '.join(issue.tags)}")
            print(f"   Created: {issue.created_at[:19]}")
    
    def print_summary(self):
        """Print issue summary"""
        summary = self.get_summary()
        
        print("\n📊 Issue Summary")
        print("=" * 40)
        print(f"Total Issues: {summary['total']}")
        
        if summary['by_status']:
            print("\nBy Status:")
            for status, count in summary['by_status'].items():
                print(f"  {status}: {count}")
        
        if summary['by_severity']:
            print("\nBy Severity:")
            for severity, count in summary['by_severity'].items():
                print(f"  {severity}: {count}")
        
        if summary['by_service']:
            print("\nBy Service:")
            for service, count in summary['by_service'].items():
                print(f"  {service}: {count}")


def main():
    """CLI for issue tracker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PM Claude Issue Tracker")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add issue
    add_parser = subparsers.add_parser('add', help='Add a new issue')
    add_parser.add_argument('service', help='Service name')
    add_parser.add_argument('title', help='Issue title')
    add_parser.add_argument('-d', '--description', help='Issue description')
    add_parser.add_argument('-s', '--severity', 
                          choices=['low', 'medium', 'high', 'critical'],
                          default='medium')
    add_parser.add_argument('-t', '--tags', nargs='+', help='Issue tags')
    
    # List issues
    list_parser = subparsers.add_parser('list', help='List issues')
    list_parser.add_argument('-s', '--service', help='Filter by service')
    list_parser.add_argument('--status', 
                           choices=['open', 'in_progress', 'resolved', 'wont_fix'])
    list_parser.add_argument('--severity',
                           choices=['low', 'medium', 'high', 'critical'])
    
    # Update issue
    update_parser = subparsers.add_parser('update', help='Update an issue')
    update_parser.add_argument('id', help='Issue ID')
    update_parser.add_argument('--status',
                             choices=['open', 'in_progress', 'resolved', 'wont_fix'])
    update_parser.add_argument('--severity',
                             choices=['low', 'medium', 'high', 'critical'])
    update_parser.add_argument('-d', '--description', help='New description')
    
    # Summary
    subparsers.add_parser('summary', help='Show issue summary')
    
    args = parser.parse_args()
    
    # Initialize tracker
    tracker = IssueTracker(Path(__file__).parent.parent)
    
    if args.command == 'add':
        issue = tracker.add_issue(
            service=args.service,
            title=args.title,
            description=args.description or "",
            severity=IssueSeverity(args.severity),
            tags=args.tags or []
        )
        print(f"✅ Added issue {issue.id}")
        tracker.print_issues([issue])
    
    elif args.command == 'list':
        issues = tracker.get_issues(
            service=args.service,
            status=IssueStatus(args.status) if args.status else None,
            severity=IssueSeverity(args.severity) if args.severity else None
        )
        tracker.print_issues(issues)
    
    elif args.command == 'update':
        issue = tracker.update_issue(
            args.id,
            status=IssueStatus(args.status) if args.status else None,
            severity=IssueSeverity(args.severity) if args.severity else None,
            description=args.description
        )
        if issue:
            print(f"✅ Updated issue {issue.id}")
            tracker.print_issues([issue])
        else:
            print(f"❌ Issue {args.id} not found")
    
    elif args.command == 'summary':
        tracker.print_summary()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()