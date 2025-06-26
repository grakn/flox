from grox import register_log_callback, setup_logging, GroxConfig

# Example: capture logs to a list
_log_buffer = []

def capture_logs(event: dict):
    _log_buffer.append(event)

config = GroxConfig.load_yaml("grox.yaml")
register_log_callback(capture_logs)
setup_logging(config)
