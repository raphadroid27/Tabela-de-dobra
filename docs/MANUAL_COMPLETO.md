# 📋 Manual Único - Sistema de Atualização Automática

## 🎯 Visão Geral

Sistema completo para atualizar automaticamente o executável do **Cálculo de Dobra** usando **pasta relativa**, funcionando independente de onde o aplicativo estiver localizado. O sistema não depende mais de caminhos de rede fixos.

---

## 👨‍💻 Para Administradores

### ✅ Disponibilizar Nova Atualização

#### Passo 1: Compilar e Preparar Executável
```bash
# 1. Compile a nova versão
pyinstaller app.spec

# 2. Copie para a pasta updates (ao lado do executável)
copy "dist\Cálculo de Dobra.exe" "pasta_do_executavel\updates\Cálculo de Dobra_new.exe"
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

### Sistema com Pasta Relativa (NOVO)

```
pasta_do_aplicativo/
├── Cálculo de Dobra.exe          # ← Executável principal
├── updates/                      # ← Pasta de atualizações (relativa)
│   ├── version.json              # ← Controle de versão
│   └── Cálculo de Dobra_new.exe  # ← Nova versão
└── backup/                       # ← Backups automáticos
    └── Cálculo de Dobra_backup_*.exe
```

### Detecção Automática de Caminhos

**Durante desenvolvimento:**
```
projeto/
├── src/
├── scripts/
└── updates/  # ← Criada na raiz do projeto
```

**Em produção (executável compilado):**
```
local_instalacao/
├── Cálculo de Dobra.exe
└── updates/  # ← Criada ao lado do executável
```

### Vantagens do Novo Sistema

✅ **Portável**: Funciona em qualquer localização  
✅ **Sem dependência de rede**: Não precisa de `Y:\` específico  
✅ **Flexível**: Funciona local ou em rede  
✅ **Automático**: Detecta automaticamente onde está  
✅ **Compatível**: Suporta desenvolvimento e produção

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
- `src/utils/update_paths.py` - **NOVO:** Gerenciamento de caminhos relativos
- `src/app.py` - Integração com menu (3 linhas!)
- `scripts/version_manager.py` - Gerenciamento unificado de versões

**Melhorias do Sistema Relativo:**
- ✅ **Detecção automática de caminhos** (desenvolvimento vs produção)
- ✅ **Portabilidade total** - funciona em qualquer local
- ✅ **Sem dependência de rede fixa** - flexível para qualquer ambiente
- ✅ **Compatibilidade retroativa** - migração automática do sistema antigo

---

## 🐛 Solução de Problemas

### ❌ "Sistema de auto-update não está disponível"
**Causa:** Pasta `updates` não encontrada
**Solução:** 
1. Verificar se existe pasta `updates` ao lado do executável
2. Criar pasta manualmente se necessário: `mkdir updates`

### ❌ Atualização não detectada
**Possíveis causas:**
1. `version.json` inválido → Verificar sintaxe JSON
2. Nova versão ≤ versão atual → Verificar versionamento
3. Cache do sistema → Aguardar 30min ou verificar manualmente
4. Pasta `updates` não existe → Sistema criará automaticamente

### ❌ Falha na atualização
**Soluções:**
1. **Espaço em disco:** Verificar espaço disponível
2. **Múltiplas instâncias:** Fechar todas as cópias do programa
3. **Permissões:** Verificar acesso de escrita na pasta
4. **Caminho inválido:** Sistema detecta automaticamente, mas verificar integridade da pasta

### ❌ Programa não reinicia após atualização
**Solução:** Executar manualmente o executável na pasta principal

### 🔄 Migração do Sistema Antigo
Se você usava o sistema anterior com `Y:\0-DESENHO\...`:

1. **Automático:** O novo sistema detecta automaticamente onde está
2. **Manual (se necessário):** Copie arquivos de `Y:\0-DESENHO\Cálculo de dobra\updates\` para a pasta `updates` local
3. **Compatibilidade:** Funciona tanto local quanto em rede

---

## 🔒 Segurança e Recuperação

**Proteções Implementadas:**
- ✅ **Backup automático** antes de cada atualização
- ✅ **Verificação de versão** (impede downgrade acidental)
- ✅ **Validação de arquivos** antes da substituição
- ✅ **Recuperação automática** em caso de falha
- ✅ **Script robusto** com timeouts e verificações
- ✅ **Detecção automática de caminhos** - funciona em qualquer local

**Em caso de falha crítica:**
1. Backup está em: `pasta_do_executavel\backup\`
2. Restaurar manualmente: copiar backup para o executável principal
3. **Sistema portável**: Funciona mesmo se movido para outro local

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

| Aspecto | Antes (Sistema Antigo) | Depois (Sistema Novo) |
|---------|----------------------|----------------------|
| **Localização** | Caminho fixo `Y:\0-DESENHO\...` | Pasta relativa ao executável |
| **Portabilidade** | Dependente de rede específica | Funciona em qualquer local |
| **Configuração** | Manual, caminho hardcoded | Automática, detecta ambiente |
| **Flexibilidade** | Apenas rede corporativa | Local, rede ou qualquer ambiente |
| **Manutenibilidade** | 6 documentos, código duplicado | 1 manual único, código limpo |
| **Detecção** | Estática | Dinâmica (dev vs produção) |
| **Migração** | Manual | Automática |

**✨ Resultado:** Sistema moderno, portável, limpo, fácil de manter e usar!

### 🔄 Principais Mudanças Técnicas:

- ✅ **Novo arquivo:** `src/utils/update_paths.py` - Gerencia caminhos automaticamente
- ✅ **AutoUpdater modernizado:** Usa funções utilitárias em vez de caminhos fixos  
- ✅ **Scripts atualizados:** `version_manager.py` e `test_auto_update.py` com lógica relativa
- ✅ **Compatibilidade total:** Funciona tanto em desenvolvimento quanto produção

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

**📞 Dúvidas?** 
- **Código principal:** `src/utils/auto_updater.py` 
- **Gerenciamento de caminhos:** `src/utils/update_paths.py`
- **Scripts de teste:** Execute `python scripts/test_auto_update.py`

**🌟 Novo Sistema de Pasta Relativa:**
- ✅ Portável - funciona em qualquer local
- ✅ Automático - detecta ambiente automaticamente  
- ✅ Flexível - suporta desenvolvimento e produção
- ✅ Compatível - migração transparente do sistema antigo
