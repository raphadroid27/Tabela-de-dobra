# Sistema Resiliente de Banco de Dados

Este documento descreve o sistema implementado para tornar o aplicativo mais resiliente a bloqueios de banco de dados.

## 📋 Recursos Implementados

### 🔧 1. Sistema de Recovery Automático
- **Desbloqueio automático** para operações críticas
- **Backup automático** antes de tentativas de desbloqueio
- **Múltiplas estratégias** de recovery
- **Logs detalhados** para auditoria

### 💾 2. Sistema de Cache Inteligente
- **Cache persistente** em memória e disco
- **Invalidação automática** quando dados são modificados
- **Fallback automático** para cache quando banco está bloqueado
- **TTL configurável** por tipo de dado

### 📊 3. Monitoramento de Bloqueios
- **Registro automático** de eventos de bloqueio
- **Estatísticas detalhadas** de frequência e duração
- **Alertas** para alta frequência de bloqueios
- **Dashboard** de monitoramento em tempo real

### 🎛️4. Interface Resiliente
- **ComboBoxes** que funcionam mesmo com banco bloqueado
- **Indicadores visuais** do status dos dados (cache vs banco)
- **Atualização automática** dos combos após mudanças

## 🚀 Como Usar

### Execução Normal do Aplicativo
O sistema é **completamente transparente**. Ao executar o aplicativo normalmente:

```bash
python -m src.app
```

- Cache é inicializado automaticamente
- Combos são preenchidos com dados do cache/banco
- Recovery automático é ativado para operações críticas

### Monitoramento de Bloqueios

#### Relatório Único
```bash
python scripts/monitor_bloqueios.py
```

#### Monitoramento Contínuo
```bash
python scripts/monitor_bloqueios.py --continuous
```

### Teste do Sistema
```bash
python -m tests.test_sistema_resiliente
```

## 📈 Configurações do Cache

### TTL (Time To Live) por Tipo
- **Materiais**: 60 minutos (dados estáticos)
- **Espessuras**: 60 minutos (dados estáticos)  
- **Canais**: 60 minutos (dados estáticos)
- **Deduções**: 5 minutos (dados dinâmicos)

### Estratégias de Invalidação
- **Automática**: Após operações CRUD
- **Por expiração**: Baseada no TTL
- **Manual**: Via `cache_manager.invalidate_cache()`

## 🔧 Estratégias de Recovery

O sistema tenta as seguintes estratégias em ordem:

1. **Desbloqueio Imediato**: PRAGMA + rollback
2. **Checkpoint Recovery**: WAL checkpoint
3. **Limpeza WAL/SHM**: Remove arquivos temporários
4. **Recovery de Emergência**: Verificação de integridade

## 📊 Configurações Otimizadas do SQLite

```sql
PRAGMA journal_mode=WAL;          -- Write-Ahead Logging
PRAGMA synchronous=NORMAL;        -- Balance segurança/performance
PRAGMA cache_size=10000;          -- Cache de 10MB
PRAGMA temp_store=MEMORY;         -- Tabelas temp em memória
PRAGMA busy_timeout=30000;        -- Timeout de 30s
PRAGMA wal_autocheckpoint=1000;   -- Checkpoint automático
```

## 🛡️ Operações Críticas

As seguintes operações ativam recovery automático:
- `initialization`: Inicialização do banco
- `critical_read`: Leituras críticas
- `critical_write`: Escritas críticas

## 📁 Estrutura de Arquivos

```
src/utils/
├── database_recovery.py     # Sistema de recovery
├── cache_manager.py         # Gerenciamento de cache
├── banco_dados.py          # Banco com recovery integrado
├── interface.py            # Interface resiliente
└── operacoes_crud.py       # CRUD com invalidação

logs/
├── database_locks.json     # Eventos de bloqueio
├── database_recovery.log   # Logs de recovery
└── app.log                # Logs principais

cache/
└── database_cache.json     # Cache persistente

scripts/
└── monitor_bloqueios.py    # Monitor de bloqueios

tests/
└── test_sistema_resiliente.py  # Testes completos
```

## 📊 Exemplo de Dashboard

```
📊 DASHBOARD DE MONITORAMENTO - BANCO DE DADOS
════════════════════════════════════════════════
🕒 Última atualização: 2025-09-03 22:33:24

🔒 BLOQUEIOS NA ÚLTIMA HORA:
   Total de bloqueios: 0
   ✅ Nenhum bloqueio detectado na última hora

🔒 BLOQUEIOS NAS ÚLTIMAS 24 HORAS:
   Total de bloqueios: 3
   Taxa de resolução: 100.0%
   Duração média: 1.25s

🔧 ESTATÍSTICAS DE RECOVERY:
   Total de recoveries: 2
   
   📋 Estratégias utilizadas:
      Checkpoint Recovery: 1 vezes
      Limpeza WAL/SHM: 1 vezes

💾 STATUS DO CACHE:
   Inicializado: ✅
   Total de entradas: 4
   Entradas válidas: 4
   Entradas expiradas: 0
   
   📊 Tipos de cache:
      materiais: 1 entradas
      espessuras: 1 entradas
      canais: 1 entradas
      deducoes: 1 entradas
```

## ⚙️ APIs do Sistema

### Cache Manager
```python
from src.utils.cache_manager import cache_manager

# Pré-carrega cache
cache_manager.preload_cache()

# Busca dados (banco ou cache)
materiais = cache_manager.get_materiais()
espessuras = cache_manager.get_espessuras()
canais = cache_manager.get_canais()
deducao = cache_manager.get_deducao("Aço", 1.0, "U 20")

# Invalida cache
cache_manager.invalidate_cache(["materiais"])

# Status do cache
status = cache_manager.get_cache_status()
```

### Database Recovery
```python
from src.utils.database_recovery import DatabaseUnlocker

# Desbloqueio manual
unlocker = DatabaseUnlocker("path/to/database.db")
success = unlocker.force_unlock(create_backup=True)

# Conexão resiliente
with resilient_database_connection("db.path", "operation_name") as conn:
    # Usa conexão normalmente
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tabela")
```

### Interface Resiliente
```python
from src.utils.interface import resilient_combo_filler

# Atualiza todos os combos
resilient_combo_filler.atualizar_todos_combos()

# Atualiza combo específico
resilient_combo_filler.preencher_combo_material(combo_widget)
```

## 🔍 Troubleshooting

### Cache não está funcionando
1. Verifique se o diretório `cache/` existe
2. Verifique permissões de escrita
3. Execute `cache_manager.force_refresh()`

### Recovery não está funcionando
1. Verifique se existem backups em `backups/database/`
2. Verifique logs em `logs/database_recovery.log`
3. Execute teste: `python -m tests.test_sistema_resiliente`

### Muitos bloqueios detectados
1. Execute monitor: `python scripts/monitor_bloqueios.py`
2. Verifique se múltiplas instâncias estão rodando
3. Considere aumentar timeouts no banco

## 🎯 Benefícios do Sistema

✅ **Disponibilidade**: Aplicativo funciona mesmo com banco bloqueado  
✅ **Performance**: Cache reduz acessos ao banco  
✅ **Resiliência**: Recovery automático resolve bloqueios  
✅ **Monitoramento**: Visibilidade completa dos problemas  
✅ **Transparência**: Funciona sem mudanças no código existente  
✅ **Auditoria**: Logs detalhados de todas as operações  

O sistema implementado garante que seu aplicativo seja muito mais robusto e confiável, especialmente em ambientes onde múltiplas instâncias podem estar rodando simultaneamente.
