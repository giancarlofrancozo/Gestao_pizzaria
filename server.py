"""
Servidor FastAPI da Pizzaria.
Execute: python server.py
Acesse: http://localhost:8000
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn 

from impressora import imprimir_item_pedido, imprimir_entrega, testar_impressora
from models.database import ConfigImpressora, ConfigCategoria

from models.database import criar_banco, popular_banco, Session, Mesa, Cardapio, Comanda, ItemPedido, Borda, StatusMesa, StatusComanda, StatusItem, Garcom, Entrega
from services.pizzaria_service import (
    listar_mesas, abrir_comanda, get_comanda_aberta, get_comanda,
    fechar_comanda, listar_cardapio, listar_bordas,
    adicionar_item, remover_item, atualizar_status_item, listar_itens_pendentes, listar_garcons, cadastrar_garcom, remover_garcom,abrir_comanda_entregas, criar_entrega, listar_entregas_ativas, atualizar_status_entrega
)

app = FastAPI(title="Pizzaria API")



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")

# ── Inicialização ─────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    criar_banco()
    popular_banco()

# ── Frontend ──────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return FileResponse("static/index.html")

# ── Login ─────────────────────────────────────────────────────────────


class LoginBody(BaseModel):
    usuario: str
    senha: str

@app.post("/api/login")
def api_login(body: LoginBody):
    session = Session()
    g = session.query(Garcom).filter_by(
        usuario=body.usuario,
        senha=body.senha,
        ativo=1
    ).first()
    session.close()
    if not g:
        raise HTTPException(401, "Usuário ou senha incorretos")
    return {"ok": True, "id": g.id, "nome": g.usuario, "admin": bool(g.admin)}
# ── Login_garçom ─────────────────────────────────────────────────────────────────────
class GarcomBody(BaseModel):
    usuario: str
    senha: str

class AbrirBody(BaseModel):
    garcom_id: Optional[int] = None

@app.post("/api/mesa/{numero}/abrir")
def api_abrir(numero: int, body: AbrirBody = None):
    garcom_id = body.garcom_id if body else None
    resultado = abrir_comanda(numero, garcom_id)
    if isinstance(resultado, str):
        raise HTTPException(400, resultado)
    return {"ok": True, "comanda_id": resultado.id}



# ── Mesas ─────────────────────────────────────────────────────────────────────

@app.get("/api/mesas")
def api_mesas():
    mesas = listar_mesas()
    return [{"id": m.id, "numero": m.numero, "capacidade": m.capacidade, "status": m.status} for m in mesas]

# ── Cardápio ──────────────────────────────────────────────────────────────────

@app.get("/api/cardapio")
def api_cardapio():
    itens = listar_cardapio()
    return [{"id": p.id, "nome": p.nome, "categoria": p.categoria, "descricao": p.descricao, "preco": p.preco} for p in itens]

@app.get("/api/bordas")
def api_bordas():
    bordas = listar_bordas()
    return [{"id": b.id, "tipo": b.tipo, "preco": b.preco} for b in bordas]

# ── Comandas ──────────────────────────────────────────────────────────────────

@app.get("/api/comandas/abertas")
def api_comandas_abertas():
    comandas = listar_comandas_abertas_serializada()
    return comandas

def serializar_comanda(c):
    return {
        "id": c.id,
        "mesa_numero": c.mesa.numero if c.mesa_id and c.mesa else "Delivery",  # <-- Protegido contra Nulo
        "abertura": c.abertura.strftime("%H:%M"),
        "status": c.status,
        "total": c.total,
        "garcom": c.garcom.usuario if c.garcom_id and c.garcom else "—",
        "itens": [serializar_item(i) for i in c.itens]
    }

def serializar_item(i):
    return {
        "id": i.id,
        "produto_nome": i.produto.nome,
        "produto2_nome": i.produto2.nome if i.produto2_id and i.produto2 else None,
        "borda": i.borda.tipo if i.borda_id and i.borda else None,
        "tamanho": i.tamanho,
        "preco_unitario": i.preco_unitario,
        "quantidade": i.quantidade,
        "observacao": i.observacao,
        "status": i.status,
        "subtotal": i.subtotal,
        "meio_a_meio": bool(i.meio_a_meio)
    }

def listar_comandas_abertas_serializada():
    session = Session()
    comandas = session.query(Comanda).filter_by(status=StatusComanda.ABERTA).all()
    resultado = []
    for c in comandas:
        if c.mesa:  # <-- Só carrega o número se a mesa existir
            _ = c.mesa.numero
        _ = c.garcom.usuario if c.garcom_id and c.garcom else None
        for i in c.itens:
            _ = i.produto.nome
            _ = i.produto2.nome if i.produto2_id else None
            _ = i.borda.tipo if i.borda_id else None
        resultado.append(serializar_comanda(c))
    session.close()
    return resultado

@app.get("/api/mesa/{numero}/comanda")
def api_comanda_mesa(numero: int):
    session = Session()
    mesa = session.query(Mesa).filter_by(numero=numero).first()
    if not mesa:
        session.close()
        raise HTTPException(404, "Mesa não encontrada")
    comanda = session.query(Comanda).filter_by(mesa_id=mesa.id, status=StatusComanda.ABERTA).first()
    if not comanda:
        session.close()
        return None
    for i in comanda.itens:
        _ = i.produto.nome
        _ = i.produto2.nome if i.produto2_id else None
        _ = i.borda.tipo if i.borda_id else None
    _ = comanda.garcom.usuario if comanda.garcom_id and comanda.garcom else None
    resultado = serializar_comanda(comanda)
    session.close()
    return resultado

@app.post("/api/comanda/{comanda_id}/fechar")
def api_fechar(comanda_id: int):
    resultado = fechar_comanda(comanda_id)
    if isinstance(resultado, str):
        raise HTTPException(400, resultado)
    return {"ok": True}

# ── Itens ─────────────────────────────────────────────────────────────────────

class ItemBody(BaseModel):
    produto_id: int
    quantidade: int = 1
    observacao: str = ""
    produto2_id: Optional[int] = None
    borda_id: Optional[int] = None
    tamanho: str = "grande"
    
@app.post("/api/comanda/{comanda_id}/item")
def api_add_item(comanda_id: int, body: ItemBody):
    resultado = adicionar_item(comanda_id, body.produto_id, body.quantidade,
                               body.observacao, body.produto2_id, body.borda_id, body.tamanho)
    if isinstance(resultado, str):
        raise HTTPException(400, resultado)
    try:
        imprimir_item_pedido(resultado)
    except Exception as e:
        print(f"Erro de impressao (nao critico): {e}")
    return {"ok": True}

@app.delete("/api/item/{item_id}")
def api_remove_item(item_id: int):
    if not remover_item(item_id):
        raise HTTPException(400, "Não foi possível remover o item")
    return {"ok": True}

@app.patch("/api/item/{item_id}/status")
def api_status_item(item_id: int, status: str):
    mapa = {"pendente": StatusItem.PENDENTE, "preparando": StatusItem.PREPARANDO,
            "pronto": StatusItem.PRONTO, "entregue": StatusItem.ENTREGUE}
    if status not in mapa:
        raise HTTPException(400, "Status inválido")
    if not atualizar_status_item(item_id, mapa[status]):
        raise HTTPException(404, "Item não encontrado")
    return {"ok": True}

# ── Cozinha ───────────────────────────────────────────────────────────────────

@app.get("/api/cozinha")
def api_cozinha():
    session = Session()
    itens = session.query(ItemPedido).filter(
        ItemPedido.status.in_([StatusItem.PENDENTE, StatusItem.PREPARANDO])
    ).order_by(ItemPedido.criado_em).all()
    resultado = []
    for i in itens:
        _ = i.produto.nome
        if i.comanda.mesa:  # <-- Proteção para exibição na cozinha se for delivery
            mesa_exibicao = i.comanda.mesa.numero
        else:
            mesa_exibicao = "Delivery"
            
        _ = i.produto2.nome if i.produto2_id else None
        _ = i.borda.tipo if i.borda_id else None
        resultado.append({
            "id": i.id,
            "mesa": mesa_exibicao,
            "produto": i.produto.nome,
            "produto2": i.produto2.nome if i.produto2_id else None,
            "borda": i.borda.tipo if i.borda_id else None,
            "tamanho": i.tamanho,
            "preco_unitario": i.preco_unitario,
            "quantidade": i.quantidade,
            "observacao": i.observacao,
            "status": i.status,
            "criado_em": i.criado_em.strftime("%H:%M")
        })
    session.close()
    return resultado
# ── Garçons ───────────────────────────────────────────────────────────────────
@app.get("/api/garcons")
def api_listar_garcons():
    garcons = listar_garcons()
    return [{"id": g.id, "usuario": g.usuario} for g in garcons]

@app.post("/api/garcons")
def api_cadastrar_garcom(body: GarcomBody):
    resultado = cadastrar_garcom(body.usuario, body.senha)
    if isinstance(resultado, str):
        raise HTTPException(400, resultado)
    return {"ok": True, "garcom_id": resultado.id}

@app.delete("/api/garcons/{garcom_id}")
def api_remover_garcom(garcom_id: int):
    from services.pizzaria_service import remover_garcom
    if not remover_garcom(garcom_id):
        raise HTTPException(404, "Garçom não encontrado")
    return {"ok": True}

# ── Delivery / Entregas ────────────────────────────────────────────────────────

class DeliveryBody(BaseModel):
    telefone: str
    nome_cliente: str
    endereco: str
    forma_pagamento: str
    troco: Optional[float] = 0.0

@app.get("/api/entregas")
def api_listar_entregas():
    """Retorna todas as entregas ativas com os respectivos dados da comanda financeira."""
    entregas = listar_entregas_ativas()
    resultado = []
    for e in entregas:
        resultado.append({
            "id": e.id,
            "comanda_id": e.comanda_id,
            "telefone": e.telefone,
            "nome_cliente": e.nome_cliente,
            "endereco": e.endereco,
            "status": e.status,
            "total": getattr(e, "total_calculado", 0.0),
            "forma_pagamento": e.forma_pagamento,
            "troco": e.troco
        })
    return resultado

@app.post("/api/entregas")
def api_criar_entregas(body: DeliveryBody):
    """Abre uma comanda de balcão/delivery e vincula os dados cadastrais do cliente."""
    comanda = abrir_comanda_entregas()
    if not comanda:
        raise HTTPException(400, "Não foi possível gerar uma comanda para a entrega.")
        
    entrega = criar_entrega(comanda.id, body.telefone, body.nome_cliente, body.endereco, body.forma_pagamento, body.troco)
    if not entrega:
        raise HTTPException(400, "Erro ao processar o vínculo cadastral da entrega.")
        
    return {"ok": True, "comanda_id": comanda.id, "entrega_id": entrega.id}

@app.patch("/api/entregas/{entrega_id}/status")
def api_atualizar_status_entrega(entrega_id: int, status: str):
    """Muda o estado logístico da entrega (ex: de 'pendente' para 'em rota')."""
    if status not in ["pendente", "em rota"]:
        raise HTTPException(400, "Status logístico inválido. Use apenas 'pendente' ou 'em rota'.")
        
    if not atualizar_status_entrega(entrega_id, status):
        raise HTTPException(404, "Registro de entrega não localizado.")
        
    return {"ok": True}

# ── Impressoras ───────────────────────────────────────────────────────────────

class ImpressoraBody(BaseModel):
    nome: str
    tipo: str = "network"
    ip: Optional[str] = None
    porta: int = 9100
    usb_vendor: Optional[str] = None
    usb_product: Optional[str] = None

class CategoriaBody(BaseModel):
    impressora_id: int
    categoria: str

@app.get("/api/impressoras")
def api_listar_impressoras():
    session = Session()
    impressoras = session.query(ConfigImpressora).filter_by(ativo=1).all()
    resultado = []
    for p in impressoras:
        cats = session.query(ConfigCategoria).filter_by(impressora_id=p.id).all()
        resultado.append({
            "id": p.id, "nome": p.nome, "ip": p.ip, "porta": p.porta,
            "categorias": [c.categoria for c in cats]
        })
    session.close()
    return resultado

@app.post("/api/impressoras")
def api_cadastrar_impressora(body: ImpressoraBody):
    session = Session()
    p = ConfigImpressora(nome=body.nome, tipo=body.tipo,
        ip=body.ip, porta=body.porta,
        usb_vendor=body.usb_vendor, usb_product=body.usb_product)
    session.add(p)
    session.commit()
    pid = p.id
    session.close()
    return {"ok": True, "id": pid}

@app.delete("/api/impressoras/{pid}")
def api_remover_impressora(pid: int):
    session = Session()
    p = session.query(ConfigImpressora).filter_by(id=pid).first()
    if not p:
        session.close()
        raise HTTPException(404, "Impressora não encontrada")
    p.ativo = 0
    session.commit()
    session.close()
    return {"ok": True}

@app.post("/api/impressoras/categoria")
def api_vincular_categoria(body: CategoriaBody):
    session = Session()
    existente = session.query(ConfigCategoria).filter_by(categoria=body.categoria).first()
    if existente:
        existente.impressora_id = body.impressora_id
    else:
        session.add(ConfigCategoria(impressora_id=body.impressora_id, categoria=body.categoria))
    session.commit()
    session.close()
    return {"ok": True}

@app.post("/api/impressoras/{pid}/testar")
def api_testar_impressora(pid: int):
    session = Session()
    p = session.query(ConfigImpressora).filter_by(id=pid).first()
    session.close()
    if not p:
        raise HTTPException(404, "Impressora não encontrada")
    ok = testar_impressora(p.ip, p.porta)
    return {"ok": ok}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)