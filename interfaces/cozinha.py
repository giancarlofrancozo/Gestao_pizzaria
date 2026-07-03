"""
Tela da cozinha — exibe pedidos pendentes em tempo real.
Execute: python interfaces/cozinha.py
"""
import sys
import os
import time
import threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.prompt import Prompt, IntPrompt
from rich.layout import Layout
from rich.text import Text
from rich import box
from datetime import datetime

from services.pizzaria_service import (
    listar_itens_pendentes, atualizar_status_item,
    StatusItem
)

console = Console()


def tabela_pedidos():
    itens = listar_itens_pendentes()
    agora = datetime.now().strftime("%H:%M:%S")

    if not itens:
        return Panel(
            f"[bold green]✅ Nenhum pedido pendente![/bold green]\n[dim]Atualizado às {agora}[/dim]",
            title="[yellow]🍕 Cozinha[/yellow]",
            border_style="green"
        )

    t = Table(
        title=f"[bold]Pedidos Pendentes — {agora}[/bold]",
        box=box.ROUNDED,
        show_lines=True
    )
    t.add_column("ID", style="dim", width=5, justify="center")
    t.add_column("Mesa", style="cyan", width=6, justify="center")
    t.add_column("Produto", style="white", width=28)
    t.add_column("Qtd", justify="center", width=5)
    t.add_column("Obs", style="dim", width=22)
    t.add_column("Status", width=13)
    t.add_column("Há (min)", justify="right", width=9)

    for item in itens:
        minutos = int((datetime.now() - item.criado_em).total_seconds() // 60)
        urgente = minutos >= 15

        if item.status == StatusItem.PENDENTE:
            status_str = "[yellow]⏳ pendente[/yellow]"
        else:
            status_str = "[blue]🔥 preparando[/blue]"

        tempo_str = f"[red bold]{minutos}[/red bold]" if urgente else str(minutos)

        t.add_row(
            str(item.id),
            str(item.comanda.mesa.numero),
            item.produto.nome,
            str(item.quantidade),
            item.observacao or "-",
            status_str,
            tempo_str,
        )

    return t


def modo_ao_vivo():
    """Atualiza a tela automaticamente a cada 5 segundos."""
    console.print("[dim]Pressione Ctrl+C para sair do modo ao vivo e entrar no interativo.[/dim]\n")
    try:
        with Live(tabela_pedidos(), refresh_per_second=0.2, screen=True) as live:
            while True:
                time.sleep(5)
                live.update(tabela_pedidos())
    except KeyboardInterrupt:
        pass


def modo_interativo():
    """Permite marcar itens como em preparo ou prontos."""
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        console.print(Panel("[bold yellow]🍕 Cozinha — Modo Interativo[/bold yellow]",
                            border_style="yellow"))
        console.print(tabela_pedidos())
        console.print()
        console.print("  [cyan]1[/cyan] — Marcar item como [blue]preparando[/blue]")
        console.print("  [cyan]2[/cyan] — Marcar item como [green]pronto[/green]")
        console.print("  [cyan]3[/cyan] — Marcar item como [dim]entregue[/dim]")
        console.print("  [cyan]0[/cyan] — Sair")

        opcao = Prompt.ask("\nEscolha", choices=["0", "1", "2", "3"])

        if opcao == "0":
            break

        mapa = {"1": StatusItem.PREPARANDO, "2": StatusItem.PRONTO, "3": StatusItem.ENTREGUE}
        novo_status = mapa[opcao]

        item_id = IntPrompt.ask("ID do item (0 = cancelar)")
        if item_id == 0:
            continue

        if atualizar_status_item(item_id, novo_status):
            console.print(f"[green]✅ Item #{item_id} atualizado para '{novo_status}'.[/green]")
        else:
            console.print(f"[red]Item #{item_id} não encontrado.[/red]")

        time.sleep(1)


def main():
    console.print(Panel("[bold yellow]🍕 Sistema de Pizzaria — Tela da Cozinha[/bold yellow]",
                        border_style="yellow"))
    console.print()
    opcao = Prompt.ask("Modo de operação",
                       choices=["vivo", "interativo"],
                       default="interativo")

    if opcao == "vivo":
        modo_ao_vivo()
        modo_interativo()
    else:
        modo_interativo()


if __name__ == "__main__":
    main()
