import sys, os
sys.path.insert(0, os.path.abspath('.'))
from models.database import criar_banco, Session, Garcom

criar_banco()
s = Session()
g = Garcom(usuario='admin', senha='1234', ativo=1, admin=1)
s.add(g)
s.commit()
s.close()
print('Usuário criado!')