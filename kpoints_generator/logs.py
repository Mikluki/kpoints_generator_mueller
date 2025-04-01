import logging
from typing import Any, Optional


class LoggerWithFileToggle:
    """Wrapper around a Logger that adds a write_to_file method."""

    def __init__(
        self,
        name: str,
        log_file: str = "kpoints_generator.log",
        level: int = logging.DEBUG,
        write_to_file_initially: bool = False,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        self.log_file = log_file
        self.level = level

        # Add console handler
        if not self.logger.handlers:
            formatter = logging.Formatter("%(name)s:%(levelname)s - %(message)s")
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Add file handler if initially enabled
        if write_to_file_initially:
            self.write_to_file(True)

    def write_to_file(
        self, enable: bool = True, custom_log_file: Optional[str] = None
    ) -> None:
        """Enable or disable writing to file."""
        if custom_log_file:
            self.log_file = custom_log_file

        # Remove any existing file handlers
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
                handler.close()

        # Add file handler if enabled
        if enable:
            formatter = logging.Formatter("%(name)s:%(levelname)s - %(message)s")
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    # Forward logging methods to the underlying logger
    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.exception(msg, *args, **kwargs)


# Create a global logger instance
LOGGER = LoggerWithFileToggle("KPGEN", "kpoints_generator.log", logging.DEBUG)


# Example usage
if __name__ == "__main__":
    LOGGER.debug("This goes to console only")

    # Enable file logging
    LOGGER.write_to_file(True)
    LOGGER.info("This goes to both console and file")
