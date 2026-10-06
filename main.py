import sys
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
from frontend.ui_manager import ConsoleApp

if __name__ == "__main__":
    app = ConsoleApp()
    app.run()
