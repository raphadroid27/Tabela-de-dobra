"""
Sistema centralizado de validação com cache para evitar validações redundantes.
Melhora performance e consistência das validações em formulários CRUD.
"""
from functools import lru_cache
from enum import Enum


class ValidationResult:
    """Resultado de uma validação."""
    
    def __init__(self, is_valid: bool, message: str = "", field: str = ""):
        self.is_valid = is_valid
        self.message = message
        self.field = field
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        return self.message if not self.is_valid else "Válido"


class ValidationRule:
    """Representa uma regra de validação."""
    
    def __init__(self, name: str, validator: Callable, message: str, priority: int = 0):
        self.name = name
        self.validator = validator
        self.message = message
        self.priority = priority  # Menor valor = maior prioridade
    
    def validate(self, value: Any, context: Dict = None) -> ValidationResult:
        """Executa a validação."""
        try:
            is_valid = self.validator(value, context or {})
            return ValidationResult(is_valid, "" if is_valid else self.message)
        except Exception as e:
            return ValidationResult(False, f"Erro na validação: {e}")


class CachedValidator:
    """Validador com cache para evitar validações repetitivas."""
    
    def __init__(self):
        self._validation_cache = {}
        self._cache_timeout = 60  # 1 minuto
        self._rules = {}
        self._field_rules = {}
        
        # Registrar validações padrão
        self._register_default_rules()
    
    def _generate_cache_key(self, field: str, value: Any, context: Dict) -> str:
        """Gera chave única para cache de validação."""
        context_str = "|".join(f"{k}={v}" for k, v in sorted(context.items()))
        return f"{field}|{value}|{context_str}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Verifica se entrada do cache ainda é válida."""
        import time
        return (time.time() - cache_entry['timestamp']) < self._cache_timeout
    
    def register_rule(self, rule: ValidationRule):
        """Registra uma nova regra de validação."""
        self._rules[rule.name] = rule
    
    def add_field_rule(self, field: str, rule_name: str):
        """Associa uma regra a um campo específico."""
        if field not in self._field_rules:
            self._field_rules[field] = []
        if rule_name in self._rules:
            self._field_rules[field].append(rule_name)
    
    def validate_field(self, field: str, value: Any, context: Dict = None) -> List[ValidationResult]:
        """
        Valida um campo específico.
        
        Args:
            field: Nome do campo
            value: Valor a ser validado
            context: Contexto adicional para validação
            
        Returns:
            Lista de resultados de validação
        """
        if context is None:
            context = {}
        
        # Verificar cache primeiro
        cache_key = self._generate_cache_key(field, value, context)
        if cache_key in self._validation_cache:
            cache_entry = self._validation_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry['results']
        
        # Executar validações
        results = []
        field_rules = self._field_rules.get(field, [])
        
        # Ordenar regras por prioridade
        sorted_rules = sorted(
            [(name, self._rules[name]) for name in field_rules if name in self._rules],
            key=lambda x: x[1].priority
        )
        
        for rule_name, rule in sorted_rules:
            result = rule.validate(value, context)
            result.field = field
            results.append(result)
            
            # Se crítico e inválido, parar validação
            if not result.is_valid and rule.priority == 0:
                break
        
        # Armazenar no cache
        import time
        self._validation_cache[cache_key] = {
            'results': results,
            'timestamp': time.time()
        }
        
        return results
    
    def validate_form(self, form_data: Dict[str, Any], context: Dict = None) -> Dict[str, List[ValidationResult]]:
        """
        Valida formulário completo.
        
        Args:
            form_data: Dados do formulário {campo: valor}
            context: Contexto adicional
            
        Returns:
            Dicionário com resultados por campo
        """
        results = {}
        for field, value in form_data.items():
            results[field] = self.validate_field(field, value, context)
        return results
    
    def is_form_valid(self, form_data: Dict[str, Any], context: Dict = None) -> bool:
        """Verifica se formulário é válido."""
        validation_results = self.validate_form(form_data, context)
        for field_results in validation_results.values():
            for result in field_results:
                if not result.is_valid:
                    return False
        return True
    
    def get_form_errors(self, form_data: Dict[str, Any], context: Dict = None) -> List[str]:
        """Retorna lista de erros do formulário."""
        validation_results = self.validate_form(form_data, context)
        errors = []
        for field_results in validation_results.values():
            for result in field_results:
                if not result.is_valid and result.message:
                    errors.append(result.message)
        return errors
    
    def clear_cache(self):
        """Limpa cache de validações."""
        self._validation_cache.clear()
    
    def _register_default_rules(self):
        """Registra regras de validação padrão."""
        
        # Validação de campo obrigatório
        self.register_rule(ValidationRule(
            "required",
            lambda value, ctx: value is not None and str(value).strip() != "",
            "Campo é obrigatório",
            priority=0
        ))
        
        # Validação de número
        self.register_rule(ValidationRule(
            "numeric",
            lambda value, ctx: self._is_numeric(value),
            "Deve ser um número válido",
            priority=1
        ))
        
        # Validação de número positivo
        self.register_rule(ValidationRule(
            "positive",
            lambda value, ctx: self._is_numeric(value) and float(value) > 0,
            "Deve ser um número positivo",
            priority=1
        ))
        
        # Validação de espessura (formato específico)
        self.register_rule(ValidationRule(
            "espessura_format",
            lambda value, ctx: self._validate_espessura(value),
            "Formato de espessura inválido (use formato 0.0)",
            priority=1
        ))
        
        # Validação de canal (formato específico)
        self.register_rule(ValidationRule(
            "canal_format",
            lambda value, ctx: self._validate_canal(value),
            "Formato de canal inválido",
            priority=1
        ))
        
        # Validação de material existente
        self.register_rule(ValidationRule(
            "material_exists",
            lambda value, ctx: self._validate_material_exists(value),
            "Material não encontrado no banco de dados",
            priority=2
        ))
        
        # Validação de duplicidade
        self.register_rule(ValidationRule(
            "unique_deducao",
            lambda value, ctx: self._validate_unique_deducao(ctx),
            "Dedução já existe para esta combinação",
            priority=2
        ))
        
        # Configurar regras por campo
        self._setup_field_rules()
    
    @lru_cache(maxsize=256)
    def _is_numeric(self, value: Any) -> bool:
        """Verifica se valor é numérico (cached)."""
        try:
            float(str(value).replace(',', '.'))
            return True
        except (ValueError, TypeError):
            return False
    
    @lru_cache(maxsize=128)
    def _validate_espessura(self, value: Any) -> bool:
        """Valida formato de espessura (cached)."""
        if not self._is_numeric(value):
            return False
        try:
            esp_value = float(str(value).replace(',', '.'))
            return 0 < esp_value <= 50  # Limites razoáveis para espessura
        except:
            return False
    
    @lru_cache(maxsize=128)
    def _validate_canal(self, value: Any) -> bool:
        """Valida formato de canal (cached)."""
        value_str = str(value).strip()
        if not value_str:
            return False
        
        # Permitir canais numéricos ou com formato especial (R=xx)
        if value_str.startswith('R='):
            try:
                float(value_str[2:])
                return True
            except:
                return False
        
        try:
            canal_num = float(value_str)
            return canal_num > 0
        except:
            return False
    
    def _validate_material_exists(self, value: Any) -> bool:
        """Valida se material existe no banco."""
        if not value:
            return False
        
        try:
            from src.utils.cache import get_materiais_cached
            materiais = get_materiais_cached()
            return any(m.nome == str(value) for m in materiais)
        except:
            return True  # Em caso de erro, assumir válido
    
    def _validate_unique_deducao(self, context: Dict) -> bool:
        """Valida unicidade de dedução."""
        required_fields = ['material_nome', 'espessura_valor', 'canal_valor']
        if not all(field in context for field in required_fields):
            return True  # Não pode validar sem contexto completo
        
        try:
            from src.utils.banco_dados import session
            from src.models.models import Material, Espessura, Canal, Deducao
            
            material = session.query(Material).filter_by(nome=context['material_nome']).first()
            espessura = session.query(Espessura).filter_by(valor=float(context['espessura_valor'])).first()
            canal = session.query(Canal).filter_by(valor=context['canal_valor']).first()
            
            if not all([material, espessura, canal]):
                return True  # Se algum não existe, deixar para outras validações
            
            existing = session.query(Deducao).filter_by(
                material_id=material.id,
                espessura_id=espessura.id,
                canal_id=canal.id
            ).first()
            
            return existing is None
            
        except:
            return True  # Em caso de erro, assumir válido
    
    def _setup_field_rules(self):
        """Configura regras por campo."""
        # Material
        self.add_field_rule('material', 'required')
        self.add_field_rule('material', 'material_exists')
        
        # Espessura
        self.add_field_rule('espessura', 'required')
        self.add_field_rule('espessura', 'espessura_format')
        
        # Canal
        self.add_field_rule('canal', 'required')
        self.add_field_rule('canal', 'canal_format')
        
        # Dedução
        self.add_field_rule('deducao', 'required')
        self.add_field_rule('deducao', 'positive')
        
        # Força
        self.add_field_rule('forca', 'numeric')  # Opcional, mas se preenchido deve ser numérico
        
        # Raio interno
        self.add_field_rule('raio_interno', 'positive')
        
        # Comprimento
        self.add_field_rule('comprimento', 'positive')


# Instância global do validador
cached_validator = CachedValidator()


def validate_field(field: str, value: Any, context: Dict = None) -> List[ValidationResult]:
    """Função conveniente para validar campo."""
    return cached_validator.validate_field(field, value, context)


def validate_form(form_data: Dict[str, Any], context: Dict = None) -> Dict[str, List[ValidationResult]]:
    """Função conveniente para validar formulário."""
    return cached_validator.validate_form(form_data, context)


def is_form_valid(form_data: Dict[str, Any], context: Dict = None) -> bool:
    """Função conveniente para verificar se formulário é válido."""
    return cached_validator.is_form_valid(form_data, context)


def get_form_errors(form_data: Dict[str, Any], context: Dict = None) -> List[str]:
    """Função conveniente para obter erros do formulário."""
    return cached_validator.get_form_errors(form_data, context)


def register_custom_rule(name: str, validator: Callable, message: str, priority: int = 1):
    """Função conveniente para registrar regra customizada."""
    rule = ValidationRule(name, validator, message, priority)
    cached_validator.register_rule(rule)


def add_field_validation(field: str, rule_name: str):
    """Função conveniente para adicionar validação a campo."""
    cached_validator.add_field_rule(field, rule_name)
