# Sistema Resiliente (SQLite + Cache)

Este documento descreve como o aplicativo foi projetado para se manter estável e rápido mesmo sob bloqueios ocasionais do SQLite e múltiplas instâncias.

## 📋 Visão Geral dos Recursos

### 🔧 1) Acesso ao Banco com Sessões Curtas
- Uso de sessões de curta duração via `get_session()` (context manager) em `src/utils/banco_dados.py`.
- SQLite configurado para evitar arquivos WAL/SHM: `journal_mode=DELETE` e `synchronous=FULL`.
- Timeout de conexão de 30s para evitar travas prolongadas.

### 💾 2) Cache Inteligente (Memória + Disco)
- Cache em memória com persistência em `CACHE_DIR/database_cache.json`.
- Escrita atômica em disco (arquivo temporário + replace) e throttling para reduzir I/O.
- TTL por tipo de dado e fallback para cache se o banco estiver indisponível.

### 🎛️ 3) Interface Resiliente
- Combos e cálculos tentam o banco; se falhar, usam o cache.
- Pré-carregamento do cache na inicialização para uma UI responsiva.

### 📊 4) Monitoramento Opcional de Bloqueios
- Monitoramento via `logs/app.log`.

## 🚀 Como Executar

O sistema é transparente para o usuário. Para iniciar:

```powershell
python -m src.app
```

- O cache será inicializado/precarregado automaticamente.
- A UI consulta o banco e faz fallback para cache quando necessário.

## 📊 Configurações do SQLite

As PRAGMAs aplicadas no connect do engine (ver `src/utils/banco_dados.py`):

```sql
PRAGMA journal_mode=DELETE;   -- Evita criar .wal e .shm (melhor p/ OneDrive e antivírus)
PRAGMA synchronous=FULL;      -- Maior integridade nas escritas
PRAGMA wal_autocheckpoint=OFF; -- Desabilitado (sem efeito em DELETE, mantido por segurança)
```

Racional: Em ambientes com diretórios sincronizados (ex.: OneDrive) e múltiplas instâncias, o modo WAL cria arquivos extras (.wal/.shm) que aumentam a chance de conflito e inspeção por antivírus. O modo DELETE reduz esses impactos.

## 📈 Cache: TTL, Invalidação e Persistência

### TTL por Tipo
- Materiais: 60 minutos
- Espessuras: 60 minutos
- Canais: 60 minutos
- Deduções: 5 minutos

### Chaves e Prefixos
- Listas: `materiais_list`, `espessuras_list`, `canais_list`.
- Deduções (item específico): `deducoes_{material}_{espessura}_{canal}`.

### Invalidação
- Após CRUD em Material: `invalidate_cache(["materiais", "deducoes"])`.
- Após CRUD em Espessura: `invalidate_cache(["espessuras", "deducoes"])`.
- Após CRUD em Canal: `invalidate_cache(["canais", "deducoes"])`.
- Após CRUD em Dedução: `invalidate_cache(["deducoes"])`.

### Persistência em Disco
- Escrita atômica: grava em arquivo temporário e substitui o JSON final (evita corrupção).
- Throttling: evita gravar com muita frequência; grava imediatamente ao encerrar ou quando forçado.

## 🧭 Sessões e Comandos entre Instâncias

- As sessões ativas e comandos do sistema são coordenados por arquivos simples (`.session`, `.cmd`).
- Motivos: simplicidade, baixa latência, menor risco de lock no SQLite (em especial no modo DELETE e em OneDrive).
- A antiga tabela `SystemControl` continua disponível para metadados de baixa frequência (ex.: versão instalada), mas não é usada para sessões/comandos.

## ⚙️ APIs Úteis

### Cache Manager
```python
from src.utils.cache_manager import cache_manager

# Preload na inicialização
cache_manager.preload_cache()

# Consultas (banco com fallback p/ cache)
materiais = cache_manager.get_materiais()
espessuras = cache_manager.get_espessuras()
canais = cache_manager.get_canais()
deducao = cache_manager.get_deducao("Aço", 1.0, "U 20")

# Invalidação
cache_manager.invalidate_cache(["materiais"])  # ou ["espessuras"], ["canais"], ["deducoes"]

# Status e manutenção
status = cache_manager.get_cache_status()
cache_manager.cleanup_expired_cache()
cache_manager.sync_cache_to_disk()
```

### Banco de Dados (sessões curtas)
```python
from src.utils.banco_dados import get_session

with get_session() as session:
   # Suas operações ORM aqui
   pass
```

## 🔍 Troubleshooting

### Cache não está atualizando
1) Verifique permissões de escrita no `CACHE_DIR`.
2) Chame `cache_manager.invalidate_cache([...])` após CRUD.
3) Forçe atualização: `cache_manager.force_refresh()`.

### Bloqueios do SQLite
1) Verifique as mensagens em `logs/app.log`.
2) Prefira rodar o app sem outras ferramentas que mantenham o DB aberto.
3) Evite colocar o DB em pastas com sync agressivo se possível.

## 🎯 Benefícios

✅ Disponibilidade: app continua operando via cache mesmo se o DB bloquear.
✅ Performance: menos I/O no banco; UI mais fluida.
✅ Robustez: sessões curtas + PRAGMAs adequadas + persistência atômica do cache.
✅ Previsibilidade: estratégia simples para sessões/comandos via arquivos.

Este arranjo foi otimizado para Windows/OneDrive e múltiplas instâncias, equilibrando segurança, desempenho e simplicidade operacional.
