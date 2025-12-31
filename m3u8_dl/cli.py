import sys
from rich.console import Console

CONSOLE = Console()

def error(message : str, exit : bool = True):
    CONSOLE.print(message,style="red")
    if exit:
        CONSOLE.print("Exiting...",style="magenta")
        sys.exit(1)
        
def warning(message : str):
    CONSOLE.print(message,style="yellow")
    
def info(message : str):
    CONSOLE.print(message,style="cyan")