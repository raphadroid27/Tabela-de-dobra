# 🔧 Cálculo de Dobra

Sistema completo para cálculos de dobra com interface moderna e sistema de atualização automática em rede.

## 🚀 Funcionalidades

- **📊 Cálculos de dobra precisos** - Suporte a diferentes materiais e espessuras
- **🔄 Atualização automática** - Sistema inteligente de auto-update em rede
- **👥 Multiusuário** - Sistema de usuários com diferentes níveis de acesso
- **💾 Banco de dados robusto** - Armazenamento de materiais, configurações e histórico
- **🖨️ Relatórios** - Geração de relatórios e impressão de resultados
- **🔒 Segurança** - Backup automático e recuperação de dados

## 📖 Documentação

### 📋 Manual Principal
- **[MANUAL_COMPLETO.md](MANUAL_COMPLETO.md)** - Manual único com todas as instruções para administradores, usuários e desenvolvedores

### 📝 Outros Arquivos
- **[CHANGELOG.md](CHANGELOG.md)** - Histórico de versões e mudanças

## 🏃‍♂️ Início Rápido

### Para Desenvolvedores
```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/Tabela-de-dobra.git

# 2. Entre na pasta
cd Tabela-de-dobra

# 3. Instale dependências
pip install -r requirements.txt

# 4. Execute o programa
python src/app.py
```

### Para Administradores
```bash
# Publicar nova atualização (comando único)
python scripts/version_manager.py
```

### Para Usuários
- Execute: `Y:\0-DESENHO\Cálculo de dobra\Cálculo de Dobra.exe`
- Atualizações são automáticas a cada 30 minutos
- Verificação manual: Menu → Utilidades → Verificar Atualizações

## 🛠️ Estrutura do Projeto

```
src/
├── app.py                 # Aplicação principal
├── components/           # Componentes da interface
├── utils/               # Utilitários (auto_updater, banco_dados, etc.)
├── models/              # Modelos de dados
└── forms/               # Formulários e dialogs

scripts/
├── version_manager.py   # Gerenciamento de versões (comando principal)
├── test_auto_update.py  # Testes do sistema de atualização
├── add_*.py             # Scripts de banco de dados
└── listar_commits.py    # Utilitário git

docs/
├── MANUAL_COMPLETO.md   # 📋 Manual único com tudo
└── CHANGELOG.md         # Histórico de versões
```

## 🔄 Sistema de Atualização

**Automatizado e transparente:**
- ✅ Verificação automática a cada 30 minutos
- ✅ Notificações inteligentes
- ✅ Backup automático antes de atualizar
- ✅ Aplicação sem interromper o trabalho
- ✅ Recuperação automática em caso de falha

**Consulte o [Manual Completo](MANUAL_COMPLETO.md) para instruções detalhadas.**

## 🤝 Contribuição

Contribuições são bem-vindas! 

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).