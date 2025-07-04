# 📋 Manual Único - Sistema de Atualização Automática

## 🎯 Visão Geral

Sistema completo para atualizar automaticamente o executável `Y:\0-DESENHO\Cálculo de dobra\Cálculo de Dobra.exe` em rede, permitindo que usuários recebam atualizações sem interromper o trabalho.

---

## 👨‍💻 Para Administradores

### ✅ Disponibilizar Nova Atualização

#### Passo 1: Compilar e Preparar Executável
```bash
# 1. Compile a nova versão
pyinstaller app.spec

# 2. Copie para o servidor de atualizações
copy "dist\Cálculo de Dobra.exe" "Y:\0-DESENHO\Cálculo de dobra\updates\Cálculo de Dobra_new.exe"
```

#### Passo 2: Configurar Atualização (Comando Único)
```bash
# Execute o gerenciador de versões
python scripts/version_manager.py
```

**O script automatiza:**
- ✅ Solicita nova versão (ex: 1.0.3)
- ✅ Solicita descrição das mudanças
- ✅ Atualiza `version.json` automaticamente
- ✅ Define se é obrigatória ou opcional
- ✅ Adiciona data de lançamento

**Resultado - version.json:**
```json
{
    "version": "1.0.3",
    "filename": "Cálculo de Dobra_new.exe",
    "mandatory": false,
    "changelog": "- Melhorias na interface\n- Correção de bugs de cálculo\n- Nova funcionalidade X",
    "release_date": "2025-01-08"
}
```

### 🔧 Tipos de Atualização

| Tipo | Configuração | Comportamento |
|------|-------------|---------------|
| **Opcional** | `"mandatory": false` | Usuário escolhe quando aplicar |
| **Obrigatória** | `"mandatory": true` | Aplicada automaticamente |

---

## 👤 Para Usuários

### 🔄 Como Funciona

**Verificação Automática:**
- Sistema verifica a cada 30 minutos
- Notificação aparece quando há atualizações disponíveis

**Verificação Manual:**
1. Menu **Utilidades** → **Verificar Atualizações**
2. Resultado aparece instantaneamente

### 📱 Processo de Atualização

1. **📢 Notificação:** "Nova versão X.Y.Z disponível"
2. **⚙️ Escolha:** "Atualizar agora" ou "Depois" (se opcional)
3. **💾 Backup:** Sistema faz backup da versão atual
4. **🔄 Atualização:** Programa fecha e aplica atualização
5. **🚀 Reinício:** Programa abre automaticamente com nova versão

---

## 🗂️ Estrutura de Arquivos

```
Y:\0-DESENHO\Cálculo de dobra\
├── Cálculo de Dobra.exe          # ← Executável atual (usuários)
├── updates\
│   ├── version.json              # ← Controle de versão
│   └── Cálculo de Dobra_new.exe  # ← Nova versão (admin)
└── backup\                       # ← Backups automáticos
    └── Cálculo de Dobra_backup_*.exe
```

---

## 🛠️ Para Desenvolvedores

### 📋 Scripts Disponíveis

```bash
# Gerenciar versões e atualizações (comando principal)
python scripts/version_manager.py

# Testar sistema de auto-update
python scripts/test_auto_update.py

# Scripts específicos do banco de dados
python scripts/add_carbono.py     # Adicionar dados de carbono
python scripts/add_h14.py         # Adicionar dados H14
python scripts/add_inox.py        # Adicionar dados inox
python scripts/listar_commits.py  # Listar commits git
```

### 🏗️ Arquitetura Principal

**Arquivos Essenciais:**
- `src/utils/auto_updater.py` - Sistema completo de auto-update
- `src/app.py` - Integração com menu (3 linhas!)
- `scripts/version_manager.py` - Gerenciamento unificado de versões

**Simplificações Realizadas:**
- ✅ Métodos duplicados removidos do AutoUpdater
- ✅ Verificação manual simplificada para 3 linhas
- ✅ Scripts de versão unificados em um só
- ✅ version.json reduzido a campos essenciais

---

## 🐛 Solução de Problemas

### ❌ "Sistema de auto-update não está disponível"
**Causa:** Problema de acesso à rede
**Solução:** Verificar conectividade com `Y:\0-DESENHO\Cálculo de dobra\updates\`

### ❌ Atualização não detectada
**Possíveis causas:**
1. `version.json` inválido → Verificar sintaxe JSON
2. Nova versão ≤ versão atual → Verificar versionamento
3. Cache do sistema → Aguardar 30min ou verificar manualmente

### ❌ Falha na atualização
**Soluções:**
1. **Espaço em disco:** Verificar espaço disponível
2. **Múltiplas instâncias:** Fechar todas as cópias do programa
3. **Permissões:** Verificar acesso de escrita na pasta

### ❌ Programa não reinicia após atualização
**Solução:** Executar manualmente: `Y:\0-DESENHO\Cálculo de dobra\Cálculo de Dobra.exe`

---

## 🔒 Segurança e Recuperação

**Proteções Implementadas:**
- ✅ **Backup automático** antes de cada atualização
- ✅ **Verificação de versão** (impede downgrade acidental)
- ✅ **Validação de arquivos** antes da substituição
- ✅ **Recuperação automática** em caso de falha
- ✅ **Script robusto** com timeouts e verificações

**Em caso de falha crítica:**
1. Backup está em: `Y:\0-DESENHO\Cálculo de dobra\backup\`
2. Restaurar manualmente: copiar backup para `Cálculo de Dobra.exe`

---

## 🚀 Fluxo Completo (Resumo)

### 🔧 Administrador:
```
1. Compila nova versão
   ↓
2. Executa: python scripts/version_manager.py
   ↓
3. Pronto! Usuários recebem atualização automaticamente
```

### ⚙️ Sistema:
```
1. Detecta nova versão (a cada 30min)
   ↓
2. Notifica usuários
   ↓
3. Aplica atualização quando solicitado
   ↓
4. Reinicia programa automaticamente
```

### 👤 Usuário:
```
1. Recebe notificação
   ↓
2. Escolhe quando aplicar (se opcional)
   ↓
3. Continua trabalhando com nova versão
```

---

## 📊 Melhorias Implementadas

| Antes | Depois |
|-------|--------|
| 6 arquivos de documentação | 1 manual único |
| 3 scripts de versão diferentes | 1 script unificado |
| Métodos duplicados no AutoUpdater | Código limpo e simplificado |
| Verificação manual complexa (25+ linhas) | Verificação simples (3 linhas) |
| version.json com campos extras | Apenas campos essenciais |

**✨ Resultado:** Sistema moderno, limpo, fácil de manter e usar!

---

## 🎯 Comandos Rápidos

**Para publicar atualização:**
```bash
python scripts/version_manager.py
```

**Para testar sistema:**
```bash
python scripts/test_auto_update.py
```

**Para verificar manualmente (usuário):**
```
Menu → Utilidades → Verificar Atualizações
```

---

**📞 Dúvidas?** Consulte o código em `src/utils/auto_updater.py` ou execute os scripts de teste.
