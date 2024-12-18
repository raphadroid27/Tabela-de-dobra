import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import usuario, deducao

class TestExcluirUsuario(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        # Setup code to create tables and add a user

    def test_excluir_usuario(self):
        usuario = self.session.query(usuario).filter_by(id=1).first()
        self.session.delete(usuario)
        self.session.commit()

        deducao_objs = self.session.query(deducao).join(usuario).filter(usuario.id == usuario.id).all()
        self.assertEqual(len(deducao_objs), 0)
        self.assertIsNone(self.session.query(usuario).filter_by(id=1).first())

    def tearDown(self):
        self.session.close()

if __name__ == '__main__':
    unittest.main()