"""
Interface do garçom — terminal interativo com Rich.
Execute: python interfaces/garcom.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box
from rich.columns import Columns
from rich.text import Text

from services.pizzaria_service import (
    listar_mesas, abrir_comanda, get_comanda_aberta,
    listar_cardapio, adicionar_item, remover_item, listar_bordas,
    fechar_comanda, Borda, StatusMesa, StatusItem,
)

console = Console()


def limpar():
    os.system("cls" if os.name == "nt" else "clear")


def cabecalho(titulo: str):
    console.print(Panel(f"[bold yellow]🍕 Pizzaria[/bold yellow]  •  [cyan]{titulo}[/cyan]",
                        border_style="yellow"))


def tela_mesas():
    """Mostra o mapa de mesas e permite selecionar uma."""
    limpar()
    cabecalho("Mapa de Mesas")

    mesas = listar_mesas()
    cards = []
    for mesa in mesas:
        cor = "green" if mesa.status == StatusMesa.LIVRE else "red"
        icone = "✅" if mesa.status == StatusMesa.LIVRE else "🔴"
        texto = Text()
        texto.append(f" {icone} Mesa {mesa.numero}\n", style=f"bold {cor}")
        texto.append(f"  {mesa.status.upper()}\n", style=cor)
        texto.append(f"  {mesa.capacidade} lugares", style="dim")
        cards.append(Panel(texto, width=16, border_style=cor))

    console.print(Columns(cards, equal=True))
    console.print()

    numero = IntPrompt.ask("[yellow]Número da mesa[/yellow] (0 = sair)")
    return numero if numero != 0 else None


def tela_cardapio() -> dict:
    """Exibe cardápio e retorna dict id→produto."""
    console.print()
    categorias = {}
    produtos = listar_cardapio()
    for p in produtos:
        categorias.setdefault(p.categoria, []).append(p)

    mapa = {}
    for cat, itens in categorias.items():
        t = Table(title=f"[bold]{cat.upper()}[/bold]", box=box.SIMPLE_HEAVY, show_header=True)
        t.add_column("Cód", style="cyan", width=5)
        t.add_column("Nome", style="white", width=26)
        t.add_column("Descrição", style="dim", width=30)
        t.add_column("Preço", style="green", justify="right")
        for p in itens:
            t.add_row(str(p.id), p.nome, p.descricao or "-", f"R$ {p.preco:.2f}")
            mapa[p.id] = p
        console.print(t)

    return mapa


def tela_comanda(comanda):
    """Exibe os itens da comanda atual."""
    t = Table(title=f"[bold]Comanda #{comanda.id} — Mesa {comanda.mesa.numero}[/bold]",
              box=box.ROUNDED)
    t.add_column("#", style="dim", width=4)
    t.add_column("Item", style="white")
    t.add_column("Qtd", justify="center", width=5)
    t.add_column("Obs", style="dim")
    t.add_column("Status", width=12)
    t.add_column("Subtotal", justify="right", style="green")
    t.add_column("Borda", style="dim", width=14)


    cores_status = {
        StatusItem.PENDENTE: "yellow",
        StatusItem.PREPARANDO: "blue",
        StatusItem.PRONTO: "green",
        StatusItem.ENTREGUE: "dim",
    }

    for item in comanda.itens:
        cor = cores_status.get(item.status, "white")
        t.add_row(
            str(item.id),
            f"{item.produto.nome} / {item.produto2.nome}" if item.meio_a_meio and item.produto2 else item.produto.nome,
            str(item.quantidade),
            item.observacao or "-",
            f"[{cor}]{item.status}[/{cor}]",
            f"R$ {item.subtotal:.2f}",
            item.borda.tipo if item.borda else "-",
        )

    console.print(t)
    console.print(f"  [bold green]Total: R$ {comanda.total:.2f}[/bold green]\n")


def gerenciar_mesa(numero_mesa: int):
    """Menu principal de uma mesa."""
    while True:
        limpar()
        cabecalho(f"Mesa {numero_mesa}")

        comanda = get_comanda_aberta(numero_mesa)

        if not comanda:
            console.print(f"[green]Mesa {numero_mesa} está livre.[/green]\n")
            opcao = Prompt.ask("O que deseja fazer?",
                               choices=["abrir", "voltar"],
                               default="abrir")
            if opcao == "voltar":
                return
            resultado = abrir_comanda(numero_mesa)
            comanda = resultado  # já existe comanda aberta, usar essa
            if comanda.abertura:
                    console.print(f"[yellow]↩ Retomando comanda #{comanda.id}[/yellow]")
            else:
                    console.print(f"[green]✅ Comanda #{comanda.id} aberta para Mesa {numero_mesa}![/green]")
            Prompt.ask("Pressione Enter")
            continue

        # Comanda aberta — exibe e oferece menu
        tela_comanda(comanda)

        console.print("[bold]Opções:[/bold]")
        console.print("  [cyan]1[/cyan] — Adicionar item")
        console.print("  [cyan]2[/cyan] — Remover item (só pendentes)")
        console.print("  [cyan]3[/cyan] — Fechar conta")
        console.print("  [cyan]0[/cyan] — Voltar")

        opcao = Prompt.ask("\nEscolha", choices=["0", "1", "2", "3"])

        if opcao == "0":
            return

        elif opcao == "1":
            mapa = tela_cardapio()
            prod_id = IntPrompt.ask("Código do produto (0 = cancelar)")
            if prod_id == 0:
                continue
            if prod_id not in mapa:
                console.print("[red]Produto não encontrado.[/red]")
                Prompt.ask("Pressione Enter")
                continue
            prod2_id = None
            if mapa[prod_id].categoria == "pizza":
                opcao = Prompt.ask("Meio a meio? (s/n)", choices=["s", "n"], default="n")
                if opcao == "s":
                    prod2_id = IntPrompt.ask("Codigo do segundo sabor (0 = cancelar)   ")
                    if prod2_id not in mapa or mapa[prod2_id].categoria != "pizza":
                        console.print("[red]Produto para meio a meio inválido.[/red]")
                        Prompt.ask("Pressione Enter")
                        continue
            borda_id = None
            if mapa[prod_id].categoria == "pizza":
                bordas = listar_bordas()
                t_bordas = Table(title="Bordas", box=box.SIMPLE_HEAVY, show_header=True)
                t_bordas.add_column("Cód", style="cyan", width=5)
                t_bordas.add_column("Tipo", style="white", width=20)
                t_bordas.add_column("Preço", style="green", justify="right")
                for b in bordas:
                    t_bordas.add_row(str(b.id), b.tipo, f"R$ {b.preco:.2f}")
                console.print(t_bordas)
                borda_id = IntPrompt.ask("Código da borda (0 = sem borda)")
                if borda_id != 0 and borda_id not in [b.id for b in bordas]:
                    console.print("[red]Borda inválida.[/red]")
                    Prompt.ask("Pressione Enter")
                    continue
                if borda_id == 0:
                    borda_id = None
            else:
                borda_id = None
            quantidade = IntPrompt.ask("Quantidade", default=1)
            obs = Prompt.ask("Observação (Enter = nenhuma)", default="")
            resultado = adicionar_item(comanda.id, prod_id, quantidade, obs, prod2_id,borda_id)
            if isinstance(resultado, str):
                console.print(f"[red]{resultado}[/red]")
            else:
                if prod2_id:
                    nome = f"{mapa[prod_id].nome} / {mapa[prod2_id].nome}"
                else:
                    nome = mapa[prod_id].nome
                if borda_id :
                    mapa_bordas = {b.id: b for b in bordas}
                    nome += f" + {mapa_bordas[borda_id].tipo}"
                console.print(f"[green]✅ {quantidade}x {nome} adicionado à comanda![/green]")  
            Prompt.ask("Pressione Enter")
        elif opcao == "3":
            tela_comanda(comanda)
            confirma = Prompt.ask(
                f"[bold]Fechar comanda #{comanda.id} — Total R$ {comanda.total:.2f}?[/bold]",
                choices=["s", "n"], default="n"
            )
            if confirma == "s":
                resultado = fechar_comanda(comanda.id)
                if isinstance(resultado, str):
                    console.print(f"[red]{resultado}[/red]")
                else:
                    console.print(f"[bold green]✅ Comanda fechada! Mesa {numero_mesa} liberada.[/bold green]")
                Prompt.ask("Pressione Enter")
                return


def main():
    console.print(Panel("[bold yellow]🍕 Sistema de Pizzaria — Módulo Garçom[/bold yellow]",
                        border_style="yellow"))

    while True:
        numero = tela_mesas()
        if numero is None:
            console.print("[dim]Saindo...[/dim]")
            break
        gerenciar_mesa(numero)



if __name__ == "__main__":
    main()
