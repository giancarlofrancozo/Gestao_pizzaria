# 🍕 Sistema de Gerenciamento para Pizzaria

Sistema completo de gerenciamento de comandas para restaurantes e pizzarias, desenvolvido em Python com interface web responsiva acessível por celular via Wi-Fi.

---

## Demonstração em Vídeo

[![Demonstração do sistema](https://img.youtube.com/vi/4vzhSETQE1I/0.jpg)](https://youtu.be/UFahEj4N4pg)

---

## Visão Geral

O sistema foi construído para substituir o controle manual de pedidos em papel, permitindo que garçons registrem pedidos pelo celular enquanto o caixa acompanha tudo em tempo real. A cozinha visualiza os pedidos em andamento e atualiza o status de cada item conforme são preparados.

---

## Funcionalidades

###  Módulo do Garçom
- Mapa visual de mesas com status em tempo real (livre/ocupada)
- Abertura de comanda por mesa
- Adição de itens com suporte a:
  - **Meio a meio** (dois sabores de pizza)
  - **Borda recheada** com preço dinâmico
  - **Tamanho** (grande / broto com desconto automático)
- Remoção de itens pendentes
- Fechamento de conta com **divisão por pessoas**
- Carrinho temporário com envio em lote

###  Módulo do Caixa (acesso restrito ao administrador)
- Painel com todas as comandas abertas e faturamento total
- Abertura de mesas diretamente do caixa
- **Seleção de itens para pagamento** com checkboxes
- **Pagamento parcial** — marca itens específicos como pagos
- Indicador visual de itens **pagos vs. restantes**
- Campo **"Valor recebido"** com cálculo automático de **troco**
- **Confirmação** quando valor recebido é menor que o total
- **Divisão da conta** baseada nos itens selecionados
- **Fechamento automático** quando todos itens estão pagos

###  Histórico de Comandas Fechadas
- Lista completa das últimas 50 comandas fechadas
- **Filtro por período** (data início / data fim)
- Estatísticas do período: faturamento, quantidade de comandas e itens
- **Reabertura de comandas** fechadas no dia atual
- Ao reabrir, a mesa é reocupada e os itens anteriores restaurados

###  Tela da Cozinha
- Lista de pedidos pendentes e em preparo
- Atualização de status: pendente → preparando → pronto → entregue
- Exibição do garçom responsável

###  Cardápio
- Listagem de produtos por categoria (pizza, bebida, sobremesa)
- **Busca** por nome, descrição ou categoria
- **Abas de categorias** com contagem de itens
- **Cadastro dinâmico** de novos itens diretamente pela interface
- **Categorias dinâmicas** — crie novas categorias personalizadas
- **Edição** de nome, categoria, preço e descrição
- **Remoção** (soft delete) de itens

###  Gerenciamento de Bordas
- Adicionar novas bordas com tipo e preço
- Remover bordas existentes
- Listagem integrada na visualização do cardápio

###  Delivery & Balcão
- Cadastro de entregas com endereço, telefone e forma de pagamento
- Pedidos de retirada no balcão
- Acompanhamento de status: pendente → em rota → entregue
- Integração com comandas para adição de itens

###  Impressoras
- Cadastro de impressoras de rede (IP/porta) e USB
- Associação de categorias de produto a impressoras específicas
- Teste de conexão
- Impressão automática de pedidos na cozinha

###  Gestão de Usuários
- Cadastro e remoção de garçons
- Login com usuário e senha
- Controle de acesso por nível (admin/garçom)

###  Sincronização Automática
- Atualização em tempo real a cada 5 segundos
- Dados não recarregam enquanto modal está aberto
- Suporte a múltiplos dispositivos simultaneamente

---

## Tecnologias Utilizadas

| Camada         | Tecnologia                          |
|----------------|-------------------------------------|
| Backend        | Python 3.13, FastAPI                |
| Banco de dados | SQLite, SQLAlchemy ORM              |
| Frontend       | HTML5, CSS3, JavaScript puro        |
| Servidor       | Uvicorn com hot-reload              |

---

## Estrutura do Projeto

```
pizzaria/
├── server.py                   ← API REST com FastAPI
├── main.py                     ← Entrada do sistema via terminal
├── criar_admin.py              ← Script para criar admin
├── impressora.py               ← Módulo de impressão térmica
├── requirements.txt
├── pizzaria.db                 ← Banco SQLite (criado automaticamente)
├── models/
│   └── database.py             ← Modelos ORM e migrações
├── services/
│   └── pizzaria_service.py     ← Lógica de negócio
├── interfaces/
│   ├── garcom.py               ← Interface terminal do garçom
│   ├── caixa.py                ← Interface terminal do caixa
│   └── cozinha.py              ← Interface terminal da cozinha
└── static/
    └── index.html              ← Frontend web responsivo (SPA)
```

---

## Instalação

**Requisitos**
- Python 3.10 ou superior
- pip

**Instalar dependências**

```bash
pip install -r requirements.txt
```

**Criar o banco de dados e o usuário administrador**

```bash
python criar_admin.py
```

Isso cria o banco `pizzaria.db` com 10 mesas, o cardápio inicial e o usuário `admin` com senha `1234`.

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
3. Copie o valor de **"Endereço IPv4"** (ex: 192.168.1.100)
4. No celular, abra o navegador e acesse `http://192.168.1.100:8000`

Caso não consiga acessar, adicione uma regra no firewall do Windows:

```bash
netsh advfirewall firewall add rule name="Pizzaria" dir=in action=allow protocol=TCP localport=8000
```

---

## Modelos do Banco de Dados

| Tabela          | Campos principais                                         |
|-----------------|-----------------------------------------------------------|
| **Mesa**        | numero, capacidade, status (livre/ocupada)                |
| **Cardapio**    | nome, categoria, descricao, preco, disponivel              |
| **Borda**       | tipo, preco, disponivel                                   |
| **Comanda**     | mesa, garcom, abertura, fechamento, status (aberta/fechada) |
| **ItemPedido**  | comanda, produto, quantidade, tamanho, preco_unitario, borda, meio_a_meio, observacao, status, pago |
| **Garcom**      | usuario, senha, ativo, admin                              |
| **Entrega**     | comanda, telefone, nome_cliente, endereco, status, forma_pagamento, troco |
| **ConfigImpressora** | nome, tipo, ip, porta, usb_vendor, usb_product, ativo |
| **ConfigCategoria**  | impressora, categoria                               |

---

## API REST

Principais endpoints:

| Método | Rota                          | Descrição                          |
|--------|-------------------------------|------------------------------------|
| POST   | `/api/login`                  | Login de garçom/admin              |
| GET    | `/api/mesas`                  | Listar mesas                       |
| POST   | `/api/mesa/{num}/abrir`       | Abrir comanda                      |
| GET    | `/api/mesa/{num}/comanda`     | Buscar comanda da mesa             |
| GET    | `/api/cardapio`               | Listar cardápio                    |
| POST   | `/api/cardapio`               | Adicionar item ao cardápio         |
| PUT    | `/api/cardapio/{id}`          | Editar item do cardápio            |
| DELETE | `/api/cardapio/{id}`          | Remover item do cardápio           |
| GET    | `/api/bordas`                 | Listar bordas                      |
| POST   | `/api/bordas`                 | Adicionar borda                    |
| DELETE | `/api/bordas/{id}`            | Remover borda                      |
| GET    | `/api/comandas/abertas`       | Listar comandas abertas            |
| GET    | `/api/comandas/fechadas`      | Listar comandas fechadas (c/ filtro) |
| POST   | `/api/comanda/{id}/fechar`    | Fechar comanda                     |
| POST   | `/api/comanda/{id}/reabrir`   | Reabrir comanda (apenas do dia)    |
| POST   | `/api/comanda/{id}/item`      | Adicionar item na comanda          |
| POST   | `/api/comanda/{id}/itens/pagar` | Marcar itens como pagos         |
| DELETE | `/api/item/{id}`              | Remover item pendente              |
| PATCH  | `/api/item/{id}/status`       | Atualizar status do item           |
| GET    | `/api/cozinha`                | Listar itens na cozinha            |
| GET    | `/api/garcons`                | Listar garçons                     |
| POST   | `/api/garcons`                | Cadastrar garçom                   |
| DELETE | `/api/garcons/{id}`           | Remover garçom                     |
| GET    | `/api/entregas`               | Listar entregas/delivery ativas    |
| POST   | `/api/entregas`               | Criar entrega/delivery             |
| PATCH  | `/api/entregas/{id}/status`   | Atualizar status da entrega        |
| GET    | `/api/impressoras`            | Listar impressoras                 |
| POST   | `/api/impressoras`            | Cadastrar impressora               |
| DELETE | `/api/impressoras/{id}`       | Remover impressora                 |
| POST   | `/api/impressoras/categoria`  | Vincular categoria à impressora    |

---

## Próximos Passos

- Relatório de faturamento detalhado por período
- Impressão de cupom não-fiscal ao fechar conta
- Gráficos e dashboard no caixa
- Deploy em nuvem para acesso externo
- Notificações push para novos pedidos

---

## Autor

Desenvolvido como projeto pessoal para estudo de desenvolvimento web e APIs REST com Python.
