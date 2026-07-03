"""
Interface do caixa — visão completa do salão e fechamento de comandas.
Execute: python interfaces/caixa.py
"""
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.layout import Layout
from rich.live import Live
from rich import box
from datetime import datetime

from services.pizzaria_service import (
    listar_mesas, listar_comandas_abertas, get_comanda_aberta,
    get_comanda, fechar_comanda, abrir_comanda, get_comanda_aberta,
    listar_cardapio, adicionar_item, remover_item, listar_bordas,
    fechar_comanda,abrir_comanda_entregas, criar_entrega, listar_entregas_ativas, atualizar_status_entrega,
    StatusMesa, StatusComanda, StatusItem
)

console = Console()


def limpar():
    os.system("cls" if os.name == "nt" else "clear")


def cabecalho(titulo: str = "Painel do Caixa"):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    console.print(Panel(
        f"[bold yellow]🍕 Pizzaria[/bold yellow]  •  [cyan]{titulo}[/cyan]  •  [dim]{agora}[/dim]",
        border_style="yellow"
    ))


def painel_geral():
    """Exibe resumo de todas as mesas e comandas abertas."""
    limpar()
    cabecalho()

    mesas = listar_mesas()
    livres = [m for m in mesas if m.status == StatusMesa.LIVRE]
    ocupadas = [m for m in mesas if m.status == StatusMesa.OCUPADA]

    console.print(
        f"  [green]✅ {len(livres)} mesa(s) livre(s)[/green]  "
        f"[red]🔴 {len(ocupadas)} mesa(s) ocupada(s)[/red]\n"
    )

    comandas = listar_comandas_abertas()

    if not comandas:
        console.print("[dim]Nenhuma comanda aberta no momento.[/dim]\n")
        return

    t = Table(title="[bold]Comandas Abertas[/bold]", box=box.ROUNDED, show_lines=True)
    t.add_column("Mesa", style="cyan", width=6, justify="center")
    t.add_column("Comanda", style="dim", width=9)
    t.add_column("Aberta às", width=10)
    t.add_column("Itens", width=6, justify="center")
    t.add_column("Pendentes", width=10, justify="center")
    t.add_column("Total", justify="right", style="bold green", width=12)

    total_geral = 0.0
    for c in comandas:
        pendentes = sum(1 for i in c.itens if i.status in [StatusItem.PENDENTE, StatusItem.PREPARANDO])
        pendente_str = f"[yellow]{pendentes}[/yellow]" if pendentes > 0 else "[dim]0[/dim]"
        t.add_row(
            str(c.mesa.numero),
            f"#{c.id}",
            c.abertura.strftime("%H:%M"),
            str(len(c.itens)),
            pendente_str,
            f"R$ {c.total:.2f}",
        )
        total_geral += c.total

    t.add_section()
    t.add_row("", "", "", "", "[bold]TOTAL[/bold]", f"[bold green]R$ {total_geral:.2f}[/bold green]")
    console.print(t)
    console.print()

def painel_entregas():
    while True:
        limpar()
        cabecalho ('Gerenciamento de Entregas')

        entregas = listar_entregas_ativas ()

        if not entregas:
            console.print("[dim]Nenhuma entrega ativa (pendente/em rota) no momento.[/dim]\n")
        else:
            t = Table(title="[bold]Entregas Ativas[/bold]", box=box.ROUNDED, show_lines=True)
            t.add_column("ID", style="cyan", width=5, justify="center")
            t.add_column("Comanda", style="dim", width=9, justify="center")
            t.add_column("Cliente", style="white", width=20)
            t.add_column("Telefone", style="white", width=15)
            t.add_column("Endereço", style="dim", width=30)
            t.add_column("Status", width=12, justify="center")
            t.add_column("Total", justify="right", style="bold green", width=10)

            cores_status = {"pendente": "yellow", "em rota": "blue"}

            for e in entregas:
                cor = cores_status.get(e.status, "white")
                t.add_row(
                    str(e.id),
                    f"#{e.comanda_id}",
                    e.nome_cliente,
                    e.telefone,
                    e.endereco,
                    f"[{cor}]{e.status.upper()}[/{cor}]",
                    f"R$ {e.comanda.total:.2f}"
                )
            console.print(t)
            console.print()

        console.print("  [cyan]1[/cyan] — Nova Entrega (Lançar Pedido)")
        console.print("  [cyan]2[/cyan] — Mudar Status (Pendente -> Em Rota)")
        console.print("  [cyan]3[/cyan] — Gerenciar Itens/Fechar Comanda de Entrega")
        console.print("  [cyan]0[/cyan] — Voltar ao Menu Principal")
        
        opcao = Prompt.ask("\nEscolha", choices=["0", "1", "2", "3"], default="0")

        if opcao == "0":
            break
        elif opcao == "1":
            lancar_nova_entrega()
        elif opcao == "2":
            alterar_status_entrega_caixa()
        elif opcao == "3":
            id_comanda = IntPrompt.ask("Digite o número da Comanda vinculada à entrega")
            detalhe_comanda(id_comanda)
def lancar_nova_entrega():
    limpar()
    cabecalho("Nova Entrega — Dados do Cliente")

    telefone = Prompt.ask("Número do cliente (Telefone)")
    nome = Prompt.ask("Nome do cliente")
    endereco = Prompt.ask("Endereço completo")
    forma_pagamento = Prompt.ask("Forma de pagamento", default="dinheiro")
    troco = float(Prompt.ask("Troco para quanto? (0 = sem troco)", default="0"))

    confirma = Prompt.ask("\nConfirmar dados e abrir pedido? (s/n)", choices=["s", "n"], default="s")
    if confirma == "s":
        comanda = abrir_comanda_entrega()
        criar_entrega(comanda.id, telefone, nome, endereco, forma_pagamento, troco)
        console.print(f"[bold green] Entrega iniciada com sucesso! Comanda [yellow]#{comanda.id}[/yellow] criada.[/bold green]")
        Prompt.ask("\nPressione Enter para ir ao cardápio e adicionar os itens")
        adicionar_item_caixa(comanda.id)

def alterar_status_entrega_caixa():
    id_entrega = IntPrompt.ask("Digite o ID da entrega que saiu para rota (0 = cancelar)")
    if id_entrega == 0:
        return
    
    if atualizar_status_entrega(id_entrega, "em rota"):
        console.print("[bold green] Status atualizado para 'Em Rota'![/bold green]")
    else:
        print("[red]Entrega não encontrada.[/red]")
    Prompt.ask("Pressione Enter")




def detalhe_comanda(comanda_id: int):
    limpar()
    comanda = get_comanda(comanda_id)
    if not comanda:
        console.print("[red]Comanda não encontrada.[/red]")
        Prompt.ask("Pressione Enter")
        return

    mesa_str = f"Mesa {comanda.mesa.numero}" if comanda.mesa else "Delivery"
    cabecalho(f"Comanda #{comanda.id} — {mesa_str}")

    t = Table(box=box.SIMPLE_HEAVY, show_header=True)
    t.add_column("#",          style="dim",   width=5)
    t.add_column("Produto",    style="white", width=30)
    t.add_column("Borda",      style="dim",   width=16)
    t.add_column("Qtd",        justify="center", width=5)
    t.add_column("Obs",        style="dim",   width=18)
    t.add_column("Status",     width=12)
    t.add_column("Subtotal",   justify="right", style="green", width=10)

    cores = {
        StatusItem.PENDENTE:   "yellow",
        StatusItem.PREPARANDO: "blue",
        StatusItem.PRONTO:     "green",
        StatusItem.ENTREGUE:   "dim",
    }

    for item in comanda.itens:
        cor = cores.get(item.status, "white")

        # nome com meio a meio
        if item.meio_a_meio and item.produto2:
            nome = f"{item.produto.nome} / {item.produto2.nome}"
        else:
            nome = item.produto.nome

        # borda
        borda_str = item.borda.tipo if item.borda else "-"

        t.add_row(
            str(item.id),
            nome,
            borda_str,
            str(item.quantidade),
            item.observacao or "-",
            f"[{cor}]{item.status}[/{cor}]",
            f"R$ {item.subtotal:.2f}",
        )

    console.print(t)

    tempo = datetime.now() - comanda.abertura
    minutos = int(tempo.total_seconds() // 60)
    console.print(f"\n  Aberta há [cyan]{minutos} min[/cyan]  |  "
                  f"[bold]Total: [green]R$ {comanda.total:.2f}[/green][/bold]\n")

    if comanda.status == StatusComanda.ABERTA:
        console.print("  [cyan]1[/cyan] — Adicionar item")
        console.print("  [cyan]2[/cyan] — Fechar comanda")
        console.print("  [cyan]0[/cyan] — Voltar")
        opcao = Prompt.ask("Escolha", choices=["0", "1", "2"], default="0")
        if opcao == "1":
            adicionar_item_caixa(comanda.id)
        elif opcao == "2":
            confirmar_fechamento(comanda.id)
    else:
        fechamento = comanda.fechamento.strftime("%d/%m/%Y %H:%M") if comanda.fechamento else "-"
        console.print(f"  Comanda [dim]fechada[/dim] em {fechamento}")
        Prompt.ask("Pressione Enter")
def confirmar_fechamento(comanda_id: int):
    comanda = get_comanda(comanda_id)
    if not comanda:
        return

    limpar()
    cabecalho(f"Fechar Comanda #{comanda.id}")

    # Cupom de fechamento
    console.print(Panel(
        f"[bold]Mesa {comanda.mesa.numero}[/bold]\n"
        f"Comanda #{comanda.id}\n"
        f"Abertura: {comanda.abertura.strftime('%d/%m/%Y %H:%M')}\n"
        f"Itens: {len(comanda.itens)}\n\n"
        f"[bold green]TOTAL: R$ {comanda.total:.2f}[/bold green]",
        title="[yellow]Confirmar Fechamento[/yellow]",
        border_style="yellow"
    ))

    confirma = Prompt.ask("Confirmar fechamento?", choices=["s", "n"], default="n")
    if confirma == "s":
        resultado = fechar_comanda(comanda_id)
        if isinstance(resultado, str):
            console.print(f"[red]{resultado}[/red]")
        else:
            console.print("[bold green]✅ Comanda fechada com sucesso! Mesa liberada.[/bold green]")
    Prompt.ask("Pressione Enter")


def buscar_mesa():
    numero = IntPrompt.ask("Número da mesa (0 = cancelar)")
    if numero == 0:
        return
    comanda = get_comanda_aberta(numero)
    if not comanda:
        console.print(f"[yellow]Mesa {numero} não tem comanda aberta.[/yellow]")
        Prompt.ask("Pressione Enter")
        return
    detalhe_comanda(comanda.id)


def menu_principal():
    console.print("\n[bold]Menu:[/bold]")
    console.print("  [cyan]1[/cyan] — Atualizar painel")
    console.print("  [cyan]2[/cyan] — Ver/fechar comanda por mesa")
    console.print("  [cyan]3[/cyan] — Ver comanda por número")
    console.print("  [cyan]4[/cyan] — Módulo Entregas / Delivery")
    console.print("  [cyan]0[/cyan] — Sair")
    return Prompt.ask("\nEscolha", choices=["0", "1", "2", "3", "4"])

def adicionar_item_caixa(comanda_id: int):
    comanda = get_comanda(comanda_id)
    if not comanda:
        console.print("[red]Comanda não encontrada.[/red]")
        Prompt.ask("Pressione Enter")
        return

    mapa = tela_cardapio()       # ← substitui o bloco manual pelo cardápio formatado
    prod_id = IntPrompt.ask("Código do produto (0 = cancelar)")
    ...
    if prod_id == 0:
        return
    if prod_id not in mapa:
        console.print("[red]Produto não encontrado.[/red]")
        Prompt.ask("Pressione Enter")
        return
    prod2_id = None
    if mapa[prod_id].categoria == "pizza":
        opcao = Prompt.ask("Meio a meio? (s/n)", choices=["s", "n"], default="n")
        if opcao == "s":
            prod2_id = IntPrompt.ask("Codigo do segundo sabor (0 = cancelar)   ")
            if prod2_id not in mapa or mapa[prod2_id].categoria != "pizza":
                console.print("[red]Produto para meio a meio inválido.[/red]")
                Prompt.ask("Pressione Enter")
                return
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
            return
        if borda_id == 0:
            borda_id = None
    quantidade = IntPrompt.ask("Quantidade", default=1)
    obs = Prompt.ask("Observação (Enter = nenhuma)", default="")
    resultado = adicionar_item(comanda.id, prod_id, quantidade, obs, prod2_id,borda_id)
    if isinstance(resultado, str):
        console.print(f"[red]{resultado}[/red]")

def tela_cardapio():
    produtos = listar_cardapio()
    categorias = {}
    for p in produtos:
        categorias.setdefault(p.categoria, []).append(p)

    mapa = {}
    for cat, itens in categorias.items():
        t = Table(title=f"[bold]{cat.upper()}[/bold]", box=box.SIMPLE_HEAVY)
        t.add_column("Cód",    style="cyan",  width=5)
        t.add_column("Nome",   style="white", width=26)
        t.add_column("Descrição", style="dim", width=30)
        t.add_column("Preço",  style="green", justify="right")
        for p in itens:
            t.add_row(str(p.id), p.nome, p.descricao or "-", f"R$ {p.preco:.2f}")
            mapa[p.id] = p
        console.print(t)

    return mapa




def main():
    console.print(Panel("[bold yellow]🍕 Sistema de Pizzaria — Módulo Caixa[/bold yellow]",
                        border_style="yellow"))

    while True:
        painel_geral()
        opcao = menu_principal()

        if opcao == "0":
            console.print("[dim]Saindo...[/dim]")
            break
        elif opcao == "1":
            continue  # painel_geral() é chamado no início do loop
        elif opcao == "2":
            buscar_mesa()
        elif opcao == "3":
            comanda_id = IntPrompt.ask("Número da comanda (0 = cancelar)")
            if comanda_id != 0:
                detalhe_comanda(comanda_id)
        elif opcao == "4":
            painel_entregas()  # <-- Chama a tela de entregas

if __name__ == "__main__":
    main()
