[# Sistema de Gerenciamento para Pizzaria

Sistema completo de gerenciamento de comandas para restaurantes e pizzarias, desenvolvido em Python com interface web responsiva acessível por celular via Wi-Fi.

---

## Demonstracao em Video

Assista ao sistema funcionando ao vivo:

[![Demonstracao do sistema](https://img.youtube.com/vi/4vzhSETQE1I/0.jpg)](https://youtu.be/UFahEj4N4pg)

---

---

## Visao Geral

O sistema foi construído para substituir o controle manual de pedidos em papel, permitindo que garçons registrem pedidos pelo celular enquanto o caixa acompanha tudo em tempo real no computador. A cozinha visualiza os pedidos em andamento e atualiza o status de cada item conforme são preparados.

---

## Funcionalidades

**Modulo do Garcom**
- Mapa visual de mesas com status em tempo real (livre/ocupada)
- Abertura de comanda por mesa
- Adicao de itens com suporte a meio a meio, borda recheada e tamanho (broto/grande)
- Remocao de itens pendentes
- Fechamento de conta

**Modulo do Caixa (acesso restrito ao administrador)**
- Painel geral com todas as mesas e comandas abertas
- Faturamento total em aberto
- Abertura de mesas e lancamento de pedidos
- Fechamento de comandas

**Tela da Cozinha**
- Lista de pedidos pendentes e em preparo
- Atualizacao de status: pendente, preparando, pronto, entregue
- Exibicao do nome do garcom responsavel por cada pedido

**Cardapio**
- Listagem de produtos por categoria (pizza, bebida, sobremesa)
- Bordas disponiveis com preco

**Gestao de Usuarios**
- Cadastro e remocao de garcons
- Login com usuario e senha
- Controle de acesso por nivel (admin/garcom)

---

## Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.13, FastAPI |
| Banco de dados | SQLite, SQLAlchemy ORM |
| Frontend | HTML, CSS, JavaScript puro |
| Interface terminal | Rich |
| Servidor | Uvicorn |

---

## Estrutura do Projeto

```
pizzaria/
├── server.py                   <- API REST com FastAPI
├── main.py                     <- Entrada do sistema via terminal
├── criar_admin.py              <- Script para criar usuario administrador
├── requirements.txt
├── models/
│   └── database.py             <- Modelos do banco de dados (ORM)
├── services/
│   └── pizzaria_service.py     <- Logica de negocio
├── interfaces/
│   ├── garcom.py               <- Interface terminal do garcom
│   ├── caixa.py                <- Interface terminal do caixa
│   └── cozinha.py              <- Interface terminal da cozinha
└── static/
    └── index.html              <- Frontend web responsivo
```

---

## Instalacao

**Requisitos**
- Python 3.10 ou superior
- pip

**Instalar dependencias**

```bash
pip install -r requirements.txt
```

**Criar o banco de dados e o usuario administrador**

```bash
python criar_admin.py
```

Isso cria o banco `pizzaria.db` com 10 mesas, o cardapio inicial e o usuario `admin` com senha `1234`.

---

## Como Executar

**Interface web (recomendado)**

```bash
python server.py
```

Acesse pelo navegador em `http://localhost:8000`.

Para acessar pelo celular na mesma rede Wi-Fi, descubra o IP do computador com `ipconfig` (Windows) e acesse `http://SEU_IP:8000`.

**Interface via terminal**

```bash
python main.py
```

---

## Acesso pelo Celular

1. Conecte o celular na mesma rede Wi-Fi do computador
2. No Windows, abra o CMD e execute `ipconfig`
3. Copie o valor de "Endereco IPv4" (ex: 192.168.1.100)
4. No celular, abra o navegador e acesse `http://192.168.1.100:8000`

Caso nao consiga acessar, adicione uma regra no firewall do Windows:

```bash
netsh advfirewall firewall add rule name="Pizzaria" dir=in action=allow protocol=TCP localport=8000
```

---

## Modelos do Banco de Dados

- **Mesa** — numero, capacidade, status
- **Cardapio** — nome, categoria, descricao, preco, disponivel
- **Borda** — tipo, preco
- **Comanda** — mesa, garcom, abertura, fechamento, status
- **ItemPedido** — comanda, produto, quantidade, tamanho, preco unitario, borda, meio a meio, observacao, status
- **Garcom** — usuario, senha, ativo, admin

---

## Proximos Passos

- Impressao de cupom em impressora termica
- Relatorio de faturamento por periodo
- Cadastro de novos itens no cardapio pela interface web
- Historico de comandas fechadas
- Deploy em nuvem para acesso externo

---

## Autor

Desenvolvido como projeto pessoal para estudo de desenvolvimento web e APIs REST com Python.
](https://youtu.be/UFahEj4N4pg)
