import sys, os
sys.path.insert(0, os.path.abspath('.'))
from models.database import criar_banco, Session, Garcom

criar_banco()
s = Session()

# Verifica se j\u00e1 existe um admin antes de criar
existente = s.query(Garcom).filter_by(usuario='admin').first()
if existente:
    print(f'Usu\u00e1rio admin j\u00e1 existe (ID {existente.id}). Nenhuma altera\u00e7\u00e3o feita.')
else:
    g = Garcom(usuario='admin', senha='1234', ativo=1, admin=1)
    s.add(g)
    s.commit()
    print('Usu\u00e1rio admin criado com sucesso!')

s.close()