# SpaceLink Utilities
from .power_control import shutdown, restart, lock_screen, sleep, hibernate
from .system_stats import get_all_stats, get_cpu_usage, get_memory_usage
from .window_manager import get_windows, focus_window, minimize_window, maximize_window
from .tts import speak, stop_speaking, get_voices
from .remote_print import get_printers, print_file, print_text
from .macro_recorder import macro_recorder
from .codec_manager import codec_manager, get_codec_status
from .network_optimizer import network_optimizer, optimize_network, get_network_status
