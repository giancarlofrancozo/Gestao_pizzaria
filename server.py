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


from models.database import criar_banco, popular_banco, Session, Mesa, Cardapio, Comanda, ItemPedido, Borda, StatusMesa, StatusComanda, StatusItem, Garcom
from services.pizzaria_service import (
    listar_mesas, abrir_comanda, get_comanda_aberta, get_comanda,
    fechar_comanda, listar_cardapio, listar_bordas,
    adicionar_item, remover_item, atualizar_status_item, listar_itens_pendentes, listar_garcons, cadastrar_garcom, remover_garcom,
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
        "mesa_numero": c.mesa.numero,
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
        _ = i.comanda.mesa.numero
        _ = i.produto2.nome if i.produto2_id else None
        _ = i.borda.tipo if i.borda_id else None
        resultado.append({
            "id": i.id,
            "mesa": i.comanda.mesa.numero,
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


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
