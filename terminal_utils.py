import sys
import select
import tty
import termios

class TerminalUtils:
    @staticmethod
    def is_data():
        """Check if there is data available on stdin."""
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    @staticmethod
    def get_key():
        """Get a keypress from stdin without blocking."""
        if TerminalUtils.is_data():
            return sys.stdin.read(1)
        return None

    @staticmethod
    def init_terminal():
        """Initialize terminal for raw input."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
        except termios.error:
            pass
        return old_settings

    @staticmethod
    def restore_terminal(old_settings):
        """Restore terminal settings."""
        fd = sys.stdin.fileno()
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except termios.error:
            pass

    @staticmethod
    def move_cursor(x: int, y: int):
        """Move terminal cursor to specified position."""
        sys.stdout.write(f"\033[{y};{x}H")
        sys.stdout.flush()