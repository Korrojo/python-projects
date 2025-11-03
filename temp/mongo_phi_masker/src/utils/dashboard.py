import webbrowser
import time
import threading

def open_dask_dashboard(scheduler_address="localhost:8787", delay=2):
    """Open Dask dashboard in browser after a delay.
    
    Args:
        scheduler_address: Dask scheduler address
        delay: Delay in seconds before opening browser
    """
    url = f"http://{scheduler_address}"
    
    def _open_browser():
        time.sleep(delay)
        webbrowser.open(url)
        
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()
    
    return url
