from flox import register_log_callback, setup_logging, FloxConfig

# Example: capture logs to a list
_log_buffer = []

def capture_logs(event: dict):
    _log_buffer.append(event)

config = FloxConfig.load_yaml("flox.yaml")
register_log_callback(capture_logs)
setup_logging(config)
