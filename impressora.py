
import socket
from models.database import Session, ConfigImpressora, ConfigCategoria

PORTA_PADRAO = 9100
TIMEOUT = 3  # segundos


def _enviar_bytes(impressora, dados: bytes) -> bool:
    try:
        if impressora.tipo == "usb":
            import usb.core
            vendor_id = int(impressora.usb_vendor, 16)
            product_id = int(impressora.usb_product, 16)
            dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
            if not dev:
                print(f"Impressora USB {impressora.usb_vendor}:{impressora.usb_product} nao encontrada")
                return False
            dev.set_configuration()
            if hasattr(dev, 'get_active_configuration'):
                cfg = dev.get_active_configuration()
            else:
                cfg = dev[0]
            intf = cfg[(0, 0)]
            ep = usb.util.find_descriptor(intf, custom_match=lambda e:
                usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
            ep.write(dados)
            return True
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(TIMEOUT)
                s.connect((impressora.ip, impressora.porta))
                s.sendall(dados)
            return True
    except Exception as e:
        print(f"Erro ao imprimir — {e}")
        return False



def _formatar_cupom(linhas: list[str]) -> bytes:

    ESC = b'\x1b'
    INIT = ESC + b'@'                    # inicializa impressora
    BOLD_ON = ESC + b'E\x01'
    BOLD_OFF = ESC + b'E\x00'
    CENTER = ESC + b'a\x01'
    LEFT = ESC + b'a\x00'
    FEED = b'\n'
    CUT = ESC + b'd\x04' + b'\x1d' + b'V\x41\x00'  # avança e corta

    resultado = INIT
    for linha in linhas:
        if linha.startswith('**') and linha.endswith('**'):
            resultado += BOLD_ON + CENTER + linha.strip('*').encode('cp850', errors='replace') + FEED + BOLD_OFF + LEFT
        elif linha.startswith('---'):
            resultado += b'-' * 32 + FEED
        else:
            resultado += LEFT + linha.encode('cp850', errors='replace') + FEED
    resultado += CUT
    return resultado


def get_impressora_por_categoria(categoria: str):
    """Retorna o objeto impressora configurada para uma categoria."""
    session = Session()
    config = session.query(ConfigCategoria).filter_by(categoria=categoria).first()
    if not config:
        session.close()
        return None
    impressora = session.query(ConfigImpressora).filter_by(
        id=config.impressora_id, ativo=1
    ).first()
    session.close()
    return impressora


def imprimir_item_pedido(item) -> bool:
    """Imprime um item recém lançado na impressora correta pela categoria."""
    categoria = item.produto.categoria
    impressora = get_impressora_por_categoria(categoria)
    if not impressora:
        print(f"Nenhuma impressora configurada para categoria '{categoria}'")
        return False

    nome = f"{item.produto.nome} / {item.produto2.nome}" if item.produto2_id and item.produto2 else item.produto.nome
    tamanho_str = f" ({item.tamanho.upper()})" if item.tamanho and item.tamanho != 'grande' else ""
    borda_str = f"Borda: {item.borda.tipo}" if item.borda_id and item.borda else ""

    linhas = [
        "**PEDIDO**",
        "---",
        f"Mesa: {item.comanda.mesa.numero if item.comanda.mesa else 'Delivery'}",
        f"Qtd: {item.quantidade}x  {nome}{tamanho_str}",
    ]
    if borda_str:
        linhas.append(borda_str)
    if item.observacao:
        linhas.append(f"Obs: {item.observacao}")
    linhas += ["---", ""]

    return _enviar_bytes(impressora, _formatar_cupom(linhas))


def imprimir_entrega(entrega, itens) -> bool:
    """Imprime resumo da entrega no caixa."""
    session = Session()
    config = session.query(ConfigCategoria).filter_by(categoria="entrega").first()
    if not config:
        session.close()
        print("Nenhuma impressora configurada para entregas")
        return False
    impressora = session.query(ConfigImpressora).filter_by(
        id=config.impressora_id, ativo=1
    ).first()
    session.close()
    if not impressora:
        return False

    linhas = [
        "**ENTREGA**",
        "---",
        f"Cliente: {entrega.nome_cliente}",
        f"Tel: {entrega.telefone}",
        f"End: {entrega.endereco}",
        f"Pgto: {entrega.forma_pagamento.upper()}",
    ]
    if entrega.troco and entrega.troco > 0:
        linhas.append(f"Troco p/ R$ {entrega.troco:.2f}")
    linhas.append("---")
    for i in itens:
        nome = f"{i.produto.nome} / {i.produto2.nome}" if i.produto2_id else i.produto.nome
        linhas.append(f"{i.quantidade}x {nome}")
    linhas += [
        "---",
        f"TOTAL: R$ {sum(i.subtotal for i in itens):.2f}",
        "",
    ]

    return _enviar_bytes(impressora, _formatar_cupom(linhas))


def testar_impressora(ip: str, porta: int = 9100) -> bool:
    linhas = ["**TESTE DE IMPRESSAO**", "---", "Impressora conectada!", ""]
    dados = _formatar_cupom(linhas)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, porta))
            s.sendall(dados)
        return True
    except Exception as e:
        print(f"Erro ao testar impressora — {e}")
        return False