"""
Ponto de entrada do sistema.
Execute: python main.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) 

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt


from models.database import criar_banco, popular_banco

console = Console()


def main():
    # Inicializa banco na primeira execução
    criar_banco()
    popular_banco()

    console.print(Panel(
        "[bold yellow]🍕 Sistema de Pizzaria[/bold yellow]\n"
        "[dim]Selecione o módulo para iniciar[/dim]",
        border_style="yellow",
        padding=(1, 4)
    ))

    console.print("  [cyan]1[/cyan] — Interface do [bold]Garçom[/bold]")
    console.print("  [cyan]2[/cyan] — Interface do [bold]Caixa[/bold]")
    console.print("  [cyan]3[/cyan] — Tela da [bold]Cozinha[/bold]")
    console.print("  [cyan]0[/cyan] — Sair")

    opcao = Prompt.ask("\nEscolha", choices=["0", "1", "2", "3"])

    if opcao == "1":
        from interfaces.garcom import main as garcom
        garcom()
    elif opcao == "2":
        from interfaces.caixa import main as caixa
        caixa()
    elif opcao == "3":
        from interfaces.cozinha import main as cozinha
        cozinha()
    else:
        console.print("[dim]Saindo...[/dim]")


if __name__ == "__main__":
    main()
