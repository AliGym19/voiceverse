#!/usr/bin/env python3
"""
Session Coordination Helper
Automates multi-session coordination using Knowledge Graph
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


class SessionCoordinator:
    def __init__(self, session_name=None, context=None, location=None):
        self.session_name = session_name or f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.context = context or "session_coordination"
        self.location = location or "global"

    def _kg_command(self, tool, params):
        """Execute Knowledge Graph MCP command"""
        # This would integrate with MCP server
        # For now, returns the command structure
        return {
            "tool": tool,
            "context": self.context,
            "location": self.location,
            **params
        }

    def register_session(self, working_dir, status="Active", project=None):
        """Register this session in coordination system"""
        observations = [
            f"Session started: {datetime.now().isoformat()}",
            f"Working directory: {working_dir}",
            f"Last heartbeat: {datetime.now().isoformat()}",
            f"Status: {status}"
        ]

        if project:
            observations.append(f"Project: {project}")

        return self._kg_command("aim_create_entities", {
            "entities": [{
                "name": self.session_name,
                "entityType": "active_session",
                "observations": observations
            }]
        })

    def update_status(self, current_file=None, task=None):
        """Update session status with current work"""
        observations = [
            f"Last heartbeat: {datetime.now().isoformat()}"
        ]

        if current_file:
            observations.append(f"Currently editing: {current_file}")

        if task:
            observations.append(f"Task: {task}")

        return self._kg_command("aim_add_observations", {
            "observations": [{
                "entityName": self.session_name,
                "contents": observations
            }]
        })

    def check_file_lock(self, file_path):
        """Check if a file is currently locked"""
        lock_name = f"lock_{Path(file_path).name}"
        return self._kg_command("aim_search_nodes", {
            "query": lock_name
        })

    def create_file_lock(self, file_path, operation, timeout_hours=2):
        """Create a lock on a file"""
        lock_name = f"lock_{Path(file_path).name}"
        timeout = datetime.now() + timedelta(hours=timeout_hours)

        entity_cmd = self._kg_command("aim_create_entities", {
            "entities": [{
                "name": lock_name,
                "entityType": "file_lock",
                "observations": [
                    f"Locked by: {self.session_name}",
                    f"Locked at: {datetime.now().isoformat()}",
                    f"Timeout: {timeout.isoformat()}",
                    f"Operation: {operation}",
                    f"File path: {file_path}"
                ]
            }]
        })

        relation_cmd = self._kg_command("aim_create_relations", {
            "relations": [{
                "from": self.session_name,
                "to": lock_name,
                "relationType": "holds_lock"
            }]
        })

        return [entity_cmd, relation_cmd]

    def release_file_lock(self, file_path):
        """Release a lock on a file"""
        lock_name = f"lock_{Path(file_path).name}"
        return self._kg_command("aim_delete_entities", {
            "entityNames": [lock_name]
        })

    def list_all_sessions(self):
        """List all active sessions"""
        return self._kg_command("aim_search_nodes", {
            "query": "active_session"
        })

    def list_all_locks(self):
        """List all file locks"""
        return self._kg_command("aim_search_nodes", {
            "query": "file_lock"
        })

    def cleanup_session(self):
        """Remove this session and all its locks"""
        return self._kg_command("aim_delete_entities", {
            "entityNames": [self.session_name]
        })

    def safe_edit_workflow(self, file_path, operation):
        """
        Safe file editing workflow:
        1. Check for locks
        2. If locked, warn and abort
        3. If not locked, create lock
        4. Return instructions to release after editing
        """
        lock_check = self.check_file_lock(file_path)

        workflow = {
            "file": file_path,
            "operation": operation,
            "steps": []
        }

        # Step 1: Check lock
        workflow["steps"].append({
            "step": 1,
            "action": "check_lock",
            "command": lock_check
        })

        # Step 2: Create lock (if safe)
        workflow["steps"].append({
            "step": 2,
            "action": "create_lock",
            "command": self.create_file_lock(file_path, operation),
            "note": "Only execute if step 1 shows no existing lock"
        })

        # Step 3: Edit file
        workflow["steps"].append({
            "step": 3,
            "action": "edit_file",
            "note": f"Perform your edit operation on {file_path}"
        })

        # Step 4: Release lock
        workflow["steps"].append({
            "step": 4,
            "action": "release_lock",
            "command": self.release_file_lock(file_path)
        })

        return workflow


def main():
    """CLI interface for session coordination"""
    import argparse

    parser = argparse.ArgumentParser(description="Session Coordination Helper")
    parser.add_argument("action", choices=[
        "register", "status", "lock", "unlock", "check",
        "list-sessions", "list-locks", "cleanup", "safe-edit"
    ])
    parser.add_argument("--session-name", help="Custom session name")
    parser.add_argument("--context", default="session_coordination", help="Knowledge graph context")
    parser.add_argument("--location", default="global", help="Storage location (global/project)")
    parser.add_argument("--file", help="File path for lock operations")
    parser.add_argument("--operation", help="Description of operation")
    parser.add_argument("--task", help="Current task description")
    parser.add_argument("--working-dir", default=".", help="Working directory")
    parser.add_argument("--project", help="Project name (e.g., kcgboxing, EHN)")

    args = parser.parse_args()

    coordinator = SessionCoordinator(args.session_name, args.context, args.location)

    if args.action == "register":
        result = coordinator.register_session(args.working_dir, project=args.project)
        print(json.dumps(result, indent=2))

    elif args.action == "status":
        result = coordinator.update_status(args.file, args.task)
        print(json.dumps(result, indent=2))

    elif args.action == "lock":
        if not args.file:
            print("Error: --file required for lock operation")
            sys.exit(1)
        result = coordinator.create_file_lock(args.file, args.operation or "editing")
        print(json.dumps(result, indent=2))

    elif args.action == "unlock":
        if not args.file:
            print("Error: --file required for unlock operation")
            sys.exit(1)
        result = coordinator.release_file_lock(args.file)
        print(json.dumps(result, indent=2))

    elif args.action == "check":
        if not args.file:
            print("Error: --file required for check operation")
            sys.exit(1)
        result = coordinator.check_file_lock(args.file)
        print(json.dumps(result, indent=2))

    elif args.action == "list-sessions":
        result = coordinator.list_all_sessions()
        print(json.dumps(result, indent=2))

    elif args.action == "list-locks":
        result = coordinator.list_all_locks()
        print(json.dumps(result, indent=2))

    elif args.action == "cleanup":
        result = coordinator.cleanup_session()
        print(json.dumps(result, indent=2))

    elif args.action == "safe-edit":
        if not args.file:
            print("Error: --file required for safe-edit workflow")
            sys.exit(1)
        workflow = coordinator.safe_edit_workflow(args.file, args.operation or "editing")
        print(json.dumps(workflow, indent=2))


if __name__ == "__main__":
    main()
