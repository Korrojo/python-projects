"""Base orchestrator for MongoDB operations."""

import subprocess
from pathlib import Path
from typing import Optional

from models.base import BaseOperationOptions


class MongoOperationResult:
    """Result of a MongoDB operation."""

    def __init__(self, success: bool, exit_code: int, stdout: str, stderr: str, duration: float):
        self.success = success
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration

    def __repr__(self) -> str:
        return (
            f"MongoOperationResult(success={self.success}, exit_code={self.exit_code}, duration={self.duration:.2f}s)"
        )


class BaseOrchestrator:
    """Base class for MongoDB operation orchestrators."""

    def __init__(self, script_name: str):
        """
        Initialize orchestrator.

        Args:
            script_name: Name of the shell script (e.g., "mongodump.sh")
        """
        self.script_name = script_name
        self.script_path = self._get_script_path()

    def _get_script_path(self) -> Path:
        """Get absolute path to the shell script."""
        # scripts are in src/scripts/<operation>/<script>.sh
        module_dir = Path(__file__).parent.parent
        scripts_dir = module_dir / "scripts"

        # Extract operation name from script name (e.g., "mongodump.sh" -> "mongodump")
        operation = self.script_name.replace(".sh", "")

        script_path = scripts_dir / operation / self.script_name

        if not script_path.exists():
            raise FileNotFoundError(f"Shell script not found: {script_path}")

        if not script_path.is_file():
            raise ValueError(f"Script path is not a file: {script_path}")

        return script_path

    def execute(self, options: BaseOperationOptions, timeout: Optional[int] = None) -> MongoOperationResult:
        """
        Execute the MongoDB operation.

        Args:
            options: Operation configuration options
            timeout: Optional timeout in seconds

        Returns:
            MongoOperationResult with execution details

        Raises:
            subprocess.TimeoutExpired: If operation exceeds timeout
            subprocess.SubprocessError: If script execution fails
        """
        # Get script arguments from options
        args = options.get_script_args()

        # Build command
        command = [str(self.script_path)] + args

        # Log command if verbose
        if options.verbose:
            print(f"Executing: {' '.join(command)}")

        # Execute script
        import time

        start_time = time.time()

        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, timeout=timeout, encoding="utf-8"
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            return MongoOperationResult(
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
            )

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            raise subprocess.TimeoutExpired(
                cmd=command,
                timeout=timeout,
                output=e.stdout.decode("utf-8") if e.stdout else "",
                stderr=e.stderr.decode("utf-8") if e.stderr else "",
            )

        except Exception as e:
            duration = time.time() - start_time
            return MongoOperationResult(success=False, exit_code=-1, stdout="", stderr=str(e), duration=duration)

    def validate_prerequisites(self) -> None:
        """
        Validate that all prerequisites are met.

        Raises:
            RuntimeError: If prerequisites are not met
        """
        # Check script exists and is executable
        if not self.script_path.exists():
            raise RuntimeError(f"Script not found: {self.script_path}")

        if not self.script_path.stat().st_mode & 0o111:
            raise RuntimeError(f"Script is not executable: {self.script_path}")

    def get_script_info(self) -> dict:
        """Get information about the script."""
        return {
            "script_name": self.script_name,
            "script_path": str(self.script_path),
            "exists": self.script_path.exists(),
            "executable": self.script_path.stat().st_mode & 0o111 if self.script_path.exists() else False,
        }
