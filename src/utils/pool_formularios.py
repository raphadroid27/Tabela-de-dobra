"""
Sistema de pool de formulários para reutilização e lazy loading.
Evita criação/destruição repetitiva de formulários.
"""
from typing import Dict, Any, Optional, Type, Callable
from collections import defaultdict
import threading
import time


class FormPool:
    """Pool de formulários reutilizáveis."""
    
    def __init__(self):
        self._pools = defaultdict(list)  # {form_class: [instances]}
        self._active_forms = {}  # {form_id: instance}
        self._form_classes = {}  # {name: class}
        self._creation_callbacks = {}  # {form_class: callback}
        self._cleanup_callbacks = {}  # {form_class: callback}
        self._max_pool_size = 3  # Máximo de instâncias por tipo
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutos
        self._lock = threading.RLock()
    
    def register_form_class(self, name: str, form_class: Type, 
                           creation_callback: Optional[Callable] = None,
                           cleanup_callback: Optional[Callable] = None):
        """
        Registra uma classe de formulário no pool.
        
        Args:
            name: Nome identificador do formulário
            form_class: Classe do formulário
            creation_callback: Callback chamado na criação
            cleanup_callback: Callback chamado na limpeza
        """
        with self._lock:
            self._form_classes[name] = form_class
            if creation_callback:
                self._creation_callbacks[form_class] = creation_callback
            if cleanup_callback:
                self._cleanup_callbacks[form_class] = cleanup_callback
    
    def get_form(self, form_name: str, *args, **kwargs) -> Any:
        """
        Obtém instância de formulário do pool ou cria nova.
        
        Args:
            form_name: Nome do formulário
            *args, **kwargs: Argumentos para criação
            
        Returns:
            Instância do formulário
        """
        with self._lock:
            if form_name not in self._form_classes:
                raise ValueError(f"Formulário '{form_name}' não registrado")
            
            form_class = self._form_classes[form_name]
            
            # Tentar reutilizar instância do pool
            if self._pools[form_class]:
                instance = self._pools[form_class].pop()
                
                # Executar callback de reativação se disponível
                if form_class in self._creation_callbacks:
                    try:
                        self._creation_callbacks[form_class](instance, *args, **kwargs)
                    except:
                        pass  # Ignorar erros em callbacks
                
                form_id = id(instance)
                self._active_forms[form_id] = instance
                return instance
            
            # Criar nova instância
            try:
                instance = form_class(*args, **kwargs)
                form_id = id(instance)
                self._active_forms[form_id] = instance
                return instance
            except Exception as e:
                print(f"Erro ao criar formulário {form_name}: {e}")
                raise
    
    def return_form(self, instance: Any, destroy: bool = False):
        """
        Retorna formulário para o pool.
        
        Args:
            instance: Instância do formulário
            destroy: Se True, destrói em vez de reutilizar
        """
        with self._lock:
            form_id = id(instance)
            
            if form_id not in self._active_forms:
                return  # Já foi retornado ou não veio do pool
            
            form_class = type(instance)
            del self._active_forms[form_id]
            
            if destroy or len(self._pools[form_class]) >= self._max_pool_size:
                # Destruir instância
                self._destroy_form_instance(instance)
            else:
                # Retornar para pool
                self._prepare_for_reuse(instance)
                self._pools[form_class].append(instance)
    
    def _prepare_for_reuse(self, instance: Any):
        """Prepara instância para reutilização."""
        form_class = type(instance)
        
        # Executar callback de limpeza
        if form_class in self._cleanup_callbacks:
            try:
                self._cleanup_callbacks[form_class](instance)
            except:
                pass  # Ignorar erros em callbacks
        
        # Limpeza padrão
        try:
            # Esconder janela se for um formulário Tkinter
            if hasattr(instance, 'withdraw'):
                instance.withdraw()
            elif hasattr(instance, 'iconify'):
                instance.iconify()
        except:
            pass
    
    def _destroy_form_instance(self, instance: Any):
        """Destrói instância de formulário."""
        try:
            if hasattr(instance, 'destroy'):
                instance.destroy()
            elif hasattr(instance, 'close'):
                instance.close()
        except:
            pass  # Ignorar erros na destruição
    
    def cleanup_inactive_forms(self, force: bool = False):
        """
        Limpa formulários inativos antigos.
        
        Args:
            force: Se True, força limpeza mesmo se não passou tempo
        """
        current_time = time.time()
        
        if not force and (current_time - self._last_cleanup) < self._cleanup_interval:
            return
        
        with self._lock:
            forms_destroyed = 0
            
            # Limpar pools grandes
            for form_class, pool in self._pools.items():
                while len(pool) > 1:  # Manter pelo menos 1 instância
                    instance = pool.pop()
                    self._destroy_form_instance(instance)
                    forms_destroyed += 1
            
            self._last_cleanup = current_time
            
            if forms_destroyed > 0:
                print(f"🧹 Pool de formulários: {forms_destroyed} instâncias limpas")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do pool."""
        with self._lock:
            stats = {
                'registered_forms': len(self._form_classes),
                'active_forms': len(self._active_forms),
                'pooled_forms': sum(len(pool) for pool in self._pools.values()),
                'pools_by_type': {
                    form_class.__name__: len(pool) 
                    for form_class, pool in self._pools.items()
                }
            }
            return stats
    
    def clear_all_pools(self):
        """Limpa todos os pools de formulários."""
        with self._lock:
            # Destruir instâncias nos pools
            for pool in self._pools.values():
                for instance in pool:
                    self._destroy_form_instance(instance)
            
            # Destruir instâncias ativas
            for instance in self._active_forms.values():
                self._destroy_form_instance(instance)
            
            self._pools.clear()
            self._active_forms.clear()


class GerenciadorFormularios:
    """Gerenciador inteligente de formulários."""
    
    def __init__(self):
        self.pool = FormPool()
        self._form_cache = {}  # Cache de configurações por formulário
        self._setup_default_forms()
    
    def _setup_default_forms(self):
        """Configura formulários padrão do sistema."""
        try:
            # Registrar formulários principais
            form_configs = [
                ('deducao', 'src.forms.form_deducao', 'FormDeducao'),
                ('material', 'src.forms.form_material', 'FormMaterial'),
                ('espessura', 'src.forms.form_espessura', 'FormEspessura'),
                ('canal', 'src.forms.form_canal', 'FormCanal'),
                ('usuario', 'src.forms.form_usuario', 'FormUsuario'),
                ('autenticacao', 'src.forms.form_aut', 'FormAutenticacao'),
                ('razao_rie', 'src.forms.form_razao_rie', 'FormRazaoRie'),
                ('spring_back', 'src.forms.form_spring_back', 'FormSpringBack'),
                ('sobre', 'src.forms.form_sobre', 'FormSobre')
            ]
            
            for form_name, module_path, class_name in form_configs:
                try:
                    # Importação lazy
                    module = __import__(module_path, fromlist=[class_name])
                    form_class = getattr(module, class_name)
                    
                    self.pool.register_form_class(
                        form_name, 
                        form_class,
                        creation_callback=self._form_creation_callback,
                        cleanup_callback=self._form_cleanup_callback
                    )
                    
                except ImportError as e:
                    print(f"⚠️ Não foi possível registrar formulário {form_name}: {e}")
                    
        except Exception as e:
            print(f"❌ Erro ao configurar formulários padrão: {e}")
    
    def _form_creation_callback(self, instance: Any, *args, **kwargs):
        """Callback executado na criação/reativação de formulário."""
        try:
            # Resetar campos se método disponível
            if hasattr(instance, 'limpar_campos'):
                instance.limpar_campos()
            
            # Reposicionar janela
            if hasattr(instance, 'geometry'):
                instance.geometry("")  # Reset position
                
        except:
            pass  # Ignorar erros
    
    def _form_cleanup_callback(self, instance: Any):
        """Callback executado na limpeza de formulário."""
        try:
            # Limpar campos
            if hasattr(instance, 'limpar_campos'):
                instance.limpar_campos()
            
            # Esconder janela
            if hasattr(instance, 'withdraw'):
                instance.withdraw()
                
        except:
            pass  # Ignorar erros
    
    def open_form(self, form_name: str, *args, **kwargs) -> Any:
        """
        Abre formulário usando pool.
        
        Args:
            form_name: Nome do formulário
            *args, **kwargs: Argumentos para o formulário
            
        Returns:
            Instância do formulário
        """
        try:
            instance = self.pool.get_form(form_name, *args, **kwargs)
            
            # Mostrar formulário
            if hasattr(instance, 'deiconify'):
                instance.deiconify()
            elif hasattr(instance, 'show'):
                instance.show()
            
            return instance
            
        except Exception as e:
            print(f"❌ Erro ao abrir formulário {form_name}: {e}")
            return None
    
    def close_form(self, instance: Any, destroy: bool = False):
        """
        Fecha formulário retornando para pool.
        
        Args:
            instance: Instância do formulário
            destroy: Se True, destrói em vez de reutilizar
        """
        self.pool.return_form(instance, destroy)
    
    def cleanup_old_forms(self):
        """Limpa formulários antigos."""
        self.pool.cleanup_inactive_forms()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do gerenciador."""
        return self.pool.get_pool_stats()


# Instância global do gerenciador
form_manager = GerenciadorFormularios()


def open_form(form_name: str, *args, **kwargs) -> Any:
    """Função conveniente para abrir formulário."""
    return form_manager.open_form(form_name, *args, **kwargs)


def close_form(instance: Any, destroy: bool = False):
    """Função conveniente para fechar formulário."""
    form_manager.close_form(instance, destroy)


def cleanup_forms():
    """Função conveniente para limpeza de formulários."""
    form_manager.cleanup_old_forms()


def get_form_stats() -> Dict[str, Any]:
    """Função conveniente para estatísticas."""
    return form_manager.get_stats()


# Context manager para formulários
class FormContext:
    """Context manager para uso seguro de formulários."""
    
    def __init__(self, form_name: str, *args, **kwargs):
        self.form_name = form_name
        self.args = args
        self.kwargs = kwargs
        self.instance = None
    
    def __enter__(self):
        self.instance = form_manager.open_form(self.form_name, *self.args, **self.kwargs)
        return self.instance
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.instance:
            form_manager.close_form(self.instance, destroy=exc_type is not None)
