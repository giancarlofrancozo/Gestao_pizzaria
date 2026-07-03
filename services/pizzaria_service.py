from datetime import datetime
from webbrowser import get

from requests import session
from sqlalchemy import false
from models.database import Session, Mesa, Cardapio, Comanda, ItemPedido, Borda, StatusMesa, StatusComanda, StatusItem, Borda, Garcom, Entrega

DESCONTO_BROTO = 10.00
# ── Entregas ────────────────────────────────────────────────────────────────────
def abrir_comanda_entregas():  
    session = Session()
    try:
        comanda = Comanda(mesa_id=None, status=StatusComanda.ABERTA)
        session.add(comanda)
        session.commit()
        session.refresh(comanda)
        _ = comanda.id
        _ = comanda.status
        return comanda
    except Exception as e:
        session.rollback()
        print(f"Erro ao abrir comanda de entrega: {e}")
        return None
    finally:
        session.close()

def criar_entrega(comanda_id: int, telefone: str, nome_cliente: str, endereco: str, forma_pagamento: str, troco: float ):
    session = Session()
    try:
        nova_entrega = Entrega(
            comanda_id=comanda_id,
            telefone=telefone,
            nome_cliente=nome_cliente,
            endereco=endereco,
            status="pendente",
            forma_pagamento=forma_pagamento,
            troco=troco
        )
        session.add(nova_entrega)
        session.commit()
        session.refresh(nova_entrega)
        return nova_entrega
    except Exception as e:
        session.rollback()
        print(f"Erro ao criar entrega: {e}")
        return None
    finally:
        session.close()

def listar_entregas_ativas():
    session = Session()
    try:
        entregas = session.query(Entrega).filter(
            Entrega.status.in_(['pendente', 'em rota'])
        ).order_by(Entrega.criado.desc()).all()
        
        for e in entregas:
            if e.comanda:
                _ = e.comanda.total
                for item in e.comanda.itens:
                    _ = item.subtotal
                    if item.produto:
                        _ = item.produto.nome
                e.total_calculado = e.comanda.total
            else:
                e.total_calculado = 0.0
        return entregas
    except Exception as e:
        print(f"Erro ao listar entregas: {e}")
        return []
    finally:
        session.close()

def atualizar_status_entrega(entrega_id: int, novo_status: str) -> bool:
    session = Session()
    try:
        entrega = session.query(Entrega).filter_by(id=entrega_id).first()
        if not entrega:
            return False
            
        entrega.status = novo_status
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Erro ao atualizar status: {e}")
        return False
    finally:
        session.close()
    

# ── Garçom ────────────────────────────────────────────────────────────────────
def listar_garcons():
    session = Session()
    garcons = session.query(Garcom).filter_by(ativo=1).order_by(Garcom.usuario).all()
    session.close()
    return garcons

def cadastrar_garcom(usuario: str, senha: str) -> Garcom | str:
    if not usuario.strip() or not senha.strip():
        return "Nome e senha não podem ser vazios."
    session = Session()
    existente = session.query(Garcom).filter_by(usuario=usuario.strip(), ativo=1).first()
    if existente:
        session.close()
        return "Usuário já existe."
    # Se existir um usuário inativo com o mesmo nome, reativa-o
    inativo = session.query(Garcom).filter_by(usuario=usuario.strip(), ativo=0).first()
    if inativo:
        inativo.ativo = 1
        inativo.senha = senha.strip()
        inativo.admin = 0  # reativação nunca preserva privilégios de admin
        session.commit()
        session.refresh(inativo)
        session.close()
        return inativo
    g = Garcom(usuario=usuario.strip(), senha=senha.strip())
    session.add(g)
    session.commit()
    session.refresh(g)
    g_id = g.id
    session.close()
    # Reabre sessão para garantir que relacionamentos sejam carregados
    session2 = Session()
    g2 = session2.query(Garcom).filter_by(id=g_id).first()
    session2.close()
    return g2

def remover_garcom(garcom_id: int) -> bool:
    session = Session()
    g = session.query(Garcom).filter_by(id=garcom_id).first()
    if not g:
        session.close()
        return False
    g.ativo = 0
    session.commit()
    session.close()
    return True
# ── Mesas ────────────────────────────────────────────────────────────────────

def listar_mesas():
    session = Session()
    mesas = session.query(Mesa).order_by(Mesa.numero).all()
    session.close()
    return mesas


def get_mesa(numero: int):
    session = Session()
    mesa = session.query(Mesa).filter_by(numero=numero).first()
    session.close()
    return mesa


# ── Cardápio ─────────────────────────────────────────────────────────────────




def listar_cardapio(categoria: str = None):
    session = Session()
    q = session.query(Cardapio).filter_by(disponivel=1)
    if categoria:
        q = q.filter_by(categoria=categoria)
    itens = q.order_by(Cardapio.categoria, Cardapio.nome).all()
    session.close()
    return itens

def listar_bordas():
    session = Session()
    bordas = session.query(Borda).filter_by(disponivel=1).order_by(Borda.tipo).all()
    session.close()
    return bordas


def get_produto(produto_id: int):
    session = Session()
    produto = session.query(Cardapio).filter_by(id=produto_id, disponivel=1).first()
    session.close()
    return produto


# ── Comandas ─────────────────────────────────────────────────────────────────

def abrir_comanda(numero_mesa: int, garcom_id: int = None) -> Comanda | str:
    """Abre comanda na mesa. Retorna a comanda ou mensagem de erro."""
    session = Session()
    mesa = session.query(Mesa).filter_by(numero=numero_mesa).first()

    if not mesa:
        session.close()
        return f"Mesa {numero_mesa} não encontrada."

    if mesa.status == StatusMesa.OCUPADA:
        session.close()
        return get_comanda_aberta(numero_mesa) or f"Mesa {numero_mesa} já está ocupada."


    
    mesa.status = StatusMesa.OCUPADA
    comanda = Comanda(mesa_id=mesa.id, garcom_id=garcom_id)
    session.add(comanda)
    session.commit()
    session.refresh(comanda)
    comanda_id = comanda.id
    session.close()
    return get_comanda(comanda_id)


def get_comanda(comanda_id: int):
    session = Session()
    comanda = session.query(Comanda).filter_by(id=comanda_id).first()
    if comanda:
        # Força carregar os dados relacionados enquanto a sessão ainda está aberta
        _ = comanda.mesa.numero
        _ = comanda.mesa.status
        _ = [(i.produto.nome, i.produto.preco, i.quantidade, 
              i.observacao, i.status, i.id, i.subtotal) for i in comanda.itens]
    session.close()
    return comanda


def get_comanda_aberta(numero_mesa: int):
    session = Session()
    mesa = session.query(Mesa).filter_by(numero=numero_mesa).first()
    if not mesa:
        session.close()
        return None
    comanda = (
        session.query(Comanda)
        .filter_by(mesa_id=mesa.id, status=StatusComanda.ABERTA)
        .first()
    )
    if comanda:
        # Força carregar os dados relacionados enquanto a sessão ainda está aberta
        _ = comanda.mesa.numero
        _ = comanda.mesa.status
        _ = [(i.produto.nome, i.produto.preco, i.quantidade,
              i.observacao, i.status, i.id, i.subtotal) for i in comanda.itens]
    session.close()
    return comanda


def listar_comandas_fechadas(data_inicio=None, data_fim=None):
    """Retorna comandas fechadas com filtro opcional por data."""
    session = Session()
    q = session.query(Comanda).filter_by(status=StatusComanda.FECHADA)
    
    if data_inicio:
        q = q.filter(Comanda.fechamento >= data_inicio)
    if data_fim:
        from datetime import timedelta
        data_fim_ajustada = data_fim + timedelta(days=1)  # inclui o dia inteiro
        q = q.filter(Comanda.fechamento < data_fim_ajustada)
    
    comandas = q.order_by(Comanda.fechamento.desc()).limit(50).all()
    for c in comandas:
        if c.mesa:
            _ = c.mesa.numero
        _ = c.garcom.usuario if c.garcom_id and c.garcom else None
        for i in c.itens:
            _ = i.produto.nome
            _ = i.produto2.nome if i.produto2_id else None
            _ = i.borda  # carrega o relacionamento borda (pode ser None)
            if i.borda:
                _ = i.borda.tipo
                _ = i.borda.preco  # pré-carrega também o preço para o subtotal
    session.close()
    return comandas


def listar_comandas_abertas():
    session = Session()
    comandas = session.query(Comanda).filter_by(status=StatusComanda.ABERTA).all()
    for c in comandas:
        _ = c.mesa.numero
        _ = c.mesa.status
        for i in c.itens:
            _ = i.produto.nome
            _ = i.produto.preco
            _ = i.produto2.nome if i.produto2_id else None
            _ = i.produto2.preco if i.produto2_id else None
            _ = i.borda  # carrega o relacionamento borda (pode ser None)
            if i.borda:
                _ = i.borda.tipo
                _ = i.borda.preco
            _ = i.meio_a_meio
            _ = i.subtotal
    session.close()
    return comandas

def reabrir_comanda(comanda_id: int):
    """Reabre uma comanda fechada do dia atual e reocupa a mesa."""
    session = Session()
    try:
        comanda = session.query(Comanda).filter_by(id=comanda_id, status=StatusComanda.FECHADA).first()
        if not comanda:
            session.close()
            return "Comanda não encontrada ou já está aberta."
        
        # Só permite reabrir comandas do dia atual
        if comanda.fechamento and comanda.fechamento.date() != datetime.now().date():
            session.close()
            return "Só é possível reabrir comandas fechadas hoje."
        
        comanda.status = StatusComanda.ABERTA
        comanda.fechamento = None
        
        if comanda.mesa_id and comanda.mesa:
            comanda.mesa.status = StatusMesa.OCUPADA
        
        session.commit()
        session.close()
        return comanda
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Erro ao reabrir comanda: {e}")
        return f"Erro interno: {e}"


def fechar_comanda(comanda_id: int):
    """Fecha a comanda financeira e libera a mesa física (se houver uma)."""
    session = Session()
    try:
        # 1. Busca a comanda correspondente
        comanda = session.query(Comanda).filter_by(id=comanda_id, status=StatusComanda.ABERTA).first()
        if not comanda:
            session.close()
            return "Comanda não encontrada ou já fechada."

        comanda.status = StatusComanda.FECHADA
        comanda.fechamento = datetime.now()

        if comanda.mesa_id and comanda.mesa:
            comanda.mesa.status = StatusMesa.LIVRE
            
        entrega = session.query(Entrega).filter_by(comanda_id=comanda_id).first()
        if entrega:
            entrega.status = "entregue" 
        session.commit()
        session.close()
        return comanda
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Erro ao fechar comanda: {e}")
        return f"Erro interno: {e}"


# ── Itens de pedido ───────────────────────────────────────────────────────────

def adicionar_item(comanda_id: int, produto_id: int, quantidade: int = 1, obs: str = "", produto2_id: int = None, borda_id: int = None, tamanho: str = "grande") -> ItemPedido | str:
    session = Session()

    comanda = session.query(Comanda).filter_by(id=comanda_id, status=StatusComanda.ABERTA).first()
    if not comanda:
        session.close()
        return "Comanda não encontrada ou já fechada."

    produto = session.query(Cardapio).filter_by(id=produto_id, disponivel=1).first()
    if not produto:
        session.close()
        return "Produto não encontrado."

    if tamanho == "broto":
        preco_unitario = produto.preco - DESCONTO_BROTO
    else:
        preco_unitario = produto.preco

    if borda_id:
        borda = session.query(Borda).filter_by(id=borda_id).first()
        if not borda:
            session.close()
            return "Borda não encontrada."

    meio_a_meio = 0
    if produto2_id:
        produto2 = session.query(Cardapio).filter_by(id=produto2_id, disponivel=1).first()
        if not produto2:
            session.close()
            return "Produto do meio a meio não encontrado."
        if produto.categoria != "pizza" or produto2.categoria != "pizza":
            session.close()
            return "Meio a meio só é permitido para pizzas."
        meio_a_meio = 1

    item = ItemPedido(
        comanda_id=comanda_id,
        produto_id=produto_id,
        quantidade=quantidade,
        observacao=obs,
        meio_a_meio=meio_a_meio,
        produto2_id=produto2_id if meio_a_meio else None,
        borda_id=borda_id,
        tamanho=tamanho,
        preco_unitario=preco_unitario
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    item_id = item.id
    session.close()

    session2 = Session()
    item = session2.query(ItemPedido).filter_by(id=item_id).first()
    if item:
        _ = item.produto.nome
        _ = item.produto.preco
        if item.meio_a_meio and item.produto2:
            _ = item.produto2.nome
            _ = item.produto2.preco
    session2.close()
    return item
        


def atualizar_status_item(item_id: int, novo_status: StatusItem) -> bool:
    session = Session()
    item = session.query(ItemPedido).filter_by(id=item_id).first()
    if not item:
        session.close()
        return False
    item.status = novo_status
    session.commit()
    session.close()
    return True


def listar_itens_pendentes():
    """Retorna todos os itens pendentes/preparando (para tela da cozinha)."""
    session = Session()
    itens = (
        session.query(ItemPedido)
        .filter(ItemPedido.status.in_([StatusItem.PENDENTE, StatusItem.PREPARANDO]))
        .order_by(ItemPedido.criado_em)
        .all()
    )
    session.close()
    return itens


def marcar_itens_pagos(comanda_id: int, item_ids: list[int]) -> bool:
    """Marca itens específicos de uma comanda como pagos."""
    session = Session()
    try:
        comanda = session.query(Comanda).filter_by(id=comanda_id).first()
        if not comanda:
            session.close()
            return False
        
        itens = session.query(ItemPedido).filter(
            ItemPedido.id.in_(item_ids),
            ItemPedido.comanda_id == comanda_id
        ).all()
        
        for item in itens:
            item.pago = 1
        
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Erro ao marcar itens como pagos: {e}")
        return False


def remover_item(item_id: int) -> bool:
    session = Session()
    item = session.query(ItemPedido).filter_by(id=item_id).first()
    if not item or item.status != StatusItem.PENDENTE:
        session.close()
        return False
    session.delete(item)
    session.commit()
    session.close()
    return True

@property
def subtotal(self):
    if self.meio_a_meio and self.produto2:
        preco = max(self.produto.preco, self.produto2.preco)
    else:
        preco = self.produto.preco
    return self.quantidade * preco


def adicionar_item_cardapio(nome: str, categoria: str, preco: float, descricao: str = ""):
    """Adiciona um novo item ao cardápio."""
    session = Session()
    try:
        item = Cardapio(
            nome=nome.strip(),
            categoria=categoria.strip().lower(),
            preco=preco,
            descricao=descricao.strip(),
            disponivel=1
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        item_id = item.id
        session.close()
        
        session2 = Session()
        novo_item = session2.query(Cardapio).filter_by(id=item_id).first()
        session2.close()
        return novo_item
    except Exception as e:
        session.rollback()
        session.close()
        return f"Erro ao adicionar item: {e}"


def editar_item_cardapio(item_id: int, nome: str, categoria: str, preco: float, descricao: str = ""):
    """Edita um item existente do cardápio."""
    session = Session()
    try:
        item = session.query(Cardapio).filter_by(id=item_id, disponivel=1).first()
        if not item:
            session.close()
            return "Item não encontrado."
        item.nome = nome.strip()
        item.categoria = categoria.strip().lower()
        item.preco = preco
        item.descricao = descricao.strip()
        session.commit()
        session.close()
        return item
    except Exception as e:
        session.rollback()
        session.close()
        return f"Erro ao editar item: {e}"


def remover_item_cardapio(item_id: int) -> bool:
    """Remove (desativa) um item do cardápio."""
    session = Session()
    try:
        item = session.query(Cardapio).filter_by(id=item_id, disponivel=1).first()
        if not item:
            session.close()
            return False
        item.disponivel = 0
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Erro ao remover item: {e}")
        return False


def adicionar_borda(tipo: str, preco: float):
    """Adiciona uma nova borda."""
    session = Session()
    try:
        borda = Borda(tipo=tipo.strip(), preco=preco, disponivel=1)
        session.add(borda)
        session.commit()
        session.refresh(borda)
        borda_id = borda.id
        session.close()
        session2 = Session()
        nova = session2.query(Borda).filter_by(id=borda_id).first()
        session2.close()
        return nova
    except Exception as e:
        session.rollback()
        session.close()
        return f"Erro ao adicionar borda: {e}"


def remover_borda(borda_id: int) -> bool:
    """Remove (desativa) uma borda."""
    session = Session()
    try:
        borda = session.query(Borda).filter_by(id=borda_id, disponivel=1).first()
        if not borda:
            session.close()
            return False
        borda.disponivel = 0
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Erro ao remover borda: {e}")
        return False