import pytest
from flask import template_rendered
from contextlib import contextmanager
from app import app  

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

def test_index_page(client):
    """Testa se a página inicial pode ser acessada."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Formulario de' in rv.data  

def test_configurations_page(client):
    """Testa se a página de configurações pode ser acessada."""
    rv = client.get('/config')
    assert rv.status_code == 200
    

def test_get_description(client):
    """Testa a funcionalidade de obter descrição de materiais."""
    with captured_templates(app) as templates:
        rv = client.get('/get-description?material=12345')
        assert rv.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert 'description' in context
      


