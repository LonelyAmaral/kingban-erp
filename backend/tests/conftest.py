"""Configuracao do pytest para os testes unitarios."""

import sys
import os

# Adicionar o diretorio backend ao path para imports funcionarem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
