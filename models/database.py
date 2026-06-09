from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from datetime import datetime
import enum


engine = create_engine("sqlite:///pizzaria.db", echo=False)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class StatusMesa(str, enum.Enum):
    LIVRE = "livre"
    OCUPADA = "ocupada"


class StatusComanda(str, enum.Enum):
    ABERTA = "aberta"
    FECHADA = "fechada"


class StatusItem(str, enum.Enum):
    PENDENTE = "pendente"
    PREPARANDO = "preparando"
    PRONTO = "pronto"
    ENTREGUE = "entregue"


class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer, unique=True, nullable=False)
    capacidade = Column(Integer, default=4)
    status = Column(String, default=StatusMesa.LIVRE)

    comandas = relationship("Comanda", back_populates="mesa")

    def __repr__(self):
        return f"Mesa {self.numero} [{self.status}]"

class Garcom(Base):
    __tablename__ = "garcons"

    id = Column(Integer, primary_key=True)
    usuario = Column(String, nullable=False)
    senha = Column(String, nullable=False)
    ativo = Column(Integer, default=1)
    admin = Column(Integer, default=0)

    def __repr__(self):
        return f"Garçom {self.usuario}"




class Cardapio(Base):
    __tablename__ = "cardapio"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    descricao = Column(String, default="")
    preco = Column(Float, nullable=False)
    disponivel = Column(Integer, default=1)

    itens = relationship("ItemPedido", foreign_keys="ItemPedido.produto_id", back_populates="produto")

    def __repr__(self):
        return f"{self.nome} - R$ {self.preco:.2f}"


class Borda(Base):
    __tablename__ = "bordas"

    id = Column(Integer, primary_key=True)
    tipo = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    disponivel = Column(Integer, default=1)

    def __repr__(self):
        return f"{self.tipo} - R$ {self.preco:.2f}"


class Comanda(Base):
    __tablename__ = "comandas"

    id = Column(Integer, primary_key=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id"), nullable=False)
    abertura = Column(DateTime, default=datetime.now)
    fechamento = Column(DateTime, nullable=True)
    status = Column(String, default=StatusComanda.ABERTA)
    observacao = Column(String, default="")
    garcom_id = Column(Integer, ForeignKey("garcons.id"), nullable=True)
    garcom = relationship("Garcom")
    mesa = relationship("Mesa", back_populates="comandas")
    itens = relationship("ItemPedido", back_populates="comanda")  # ← sem espaço

    @property
    def total(self):
        return sum(i.subtotal for i in self.itens)

    def __repr__(self):
        return f"Comanda #{self.id} | Mesa {self.mesa.numero} | R$ {self.total:.2f}"


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True)
    comanda_id = Column(Integer, ForeignKey("comandas.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("cardapio.id"), nullable=False)
    quantidade = Column(Integer, default=1)
    observacao = Column(String, default="")
    tamanho = Column(String, default="normal")  # normal, grande
    preco_unitario = Column(Float, nullable=False)
    status = Column(String, default=StatusItem.PENDENTE)
    criado_em = Column(DateTime, default=datetime.now)
    meio_a_meio = Column(Integer, default=0)
    produto2_id = Column(Integer, ForeignKey("cardapio.id"), nullable=True)
    borda_id = Column(Integer, ForeignKey("bordas.id"), nullable=True)

    comanda = relationship("Comanda", back_populates="itens")
    produto = relationship("Cardapio", foreign_keys=[produto_id], back_populates="itens")
    produto2 = relationship("Cardapio", foreign_keys=[produto2_id])
    borda = relationship("Borda", foreign_keys=[borda_id])  # ← maiúsculo

    @property
    def subtotal(self):
        preco_borda= self.borda.preco if self.borda else 0
        preco_uini = self.preco_unitario if self.preco_unitario else self.produto.preco
        return self.quantidade * (preco_uini + preco_borda)
        
    def __repr__(self):
        return f"{self.quantidade}x {self.produto.nome} [{self.status}]"


def criar_banco():
    Base.metadata.create_all(engine)


def popular_banco():
    session = Session()

    if session.query(Mesa).count() == 0:
        for i in range(1, 11):
            session.add(Mesa(numero=i, capacidade=4 if i <= 6 else 6))

    if session.query(Borda).count() == 0:
        bordas = [
            Borda(tipo="sem borda",        preco=0.00),
            Borda(tipo="cheddar",          preco=12.00),
            Borda(tipo="catupiry",         preco=12.00),
            Borda(tipo="brigadeiro",       preco=12.00),
            Borda(tipo="chocolate branco", preco=12.00),
            Borda(tipo="mussarela",        preco=12.00),
        ]
        session.add_all(bordas)

    if session.query(Cardapio).count() == 0:
        itens = [
            Cardapio(nome="Margherita",          categoria="pizza",     preco=42.90, descricao="Molho, mussarela, tomate e manjericão"),
            Cardapio(nome="Calabresa",           categoria="pizza",     preco=44.90, descricao="Molho, mussarela e calabresa"),
            Cardapio(nome="Frango c/ Catupiry",  categoria="pizza",     preco=47.90, descricao="Molho, mussarela, frango e catupiry"),
            Cardapio(nome="Portuguesa",          categoria="pizza",     preco=49.90, descricao="Molho, mussarela, presunto, ovo e cebola"),
            Cardapio(nome="Quatro Queijos",      categoria="pizza",     preco=52.90, descricao="Mussarela, provolone, parmesão e catupiry"),
            Cardapio(nome="Pepperoni",           categoria="pizza",     preco=54.90, descricao="Molho, mussarela e pepperoni"),
            Cardapio(nome="Coca-Cola 350ml",     categoria="bebida",    preco=6.00),
            Cardapio(nome="Coca-Cola 2L",        categoria="bebida",    preco=14.00),
            Cardapio(nome="Suco Natural 500ml",  categoria="bebida",    preco=12.00),
            Cardapio(nome="Água 500ml",          categoria="bebida",    preco=4.00),
            Cardapio(nome="Cerveja 600ml",       categoria="bebida",    preco=16.00),
            Cardapio(nome="Pizza Doce Brigadeiro", categoria="sobremesa", preco=39.90),
            Cardapio(nome="Sorvete 2 bolas",     categoria="sobremesa", preco=14.00),
        ]
        session.add_all(itens)

    session.commit()
    session.close()