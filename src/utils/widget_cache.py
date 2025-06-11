"""
Sistema de cache para widgets Tkinter e otimização de loops com getattr().
Reduz custos de reflexão e melhora performance de operações de UI.
"""
from collections import defaultdict
from typing import Any, List


class WidgetCache:
    """Cache inteligente para widgets Tkinter e suas referências."""
    
    def __init__(self):
        self._widget_refs = defaultdict(dict)  # {object_id: {attr_name: widget}}
        self._widget_lists = defaultdict(list)  # {pattern: [widgets]}
        self._cleanup_callbacks = []
    
    def cache_widget(self, obj: Any, attr_name: str, widget: Any):
        """
        Armazena referência de widget no cache.
        
        Args:
            obj: Objeto que contém o widget
            attr_name: Nome do atributo
            widget: Widget a ser cached
        """
        obj_id = id(obj)
        self._widget_refs[obj_id][attr_name] = widget
    
    def get_widget(self, obj: Any, attr_name: str, default: Any = None) -> Any:
        """
        Recupera widget do cache ou usa getattr como fallback.
        
        Args:
            obj: Objeto que contém o widget
            attr_name: Nome do atributo
            default: Valor padrão se não encontrado
            
        Returns:
            Widget ou valor padrão
        """
        obj_id = id(obj)
        
        # Verificar cache primeiro
        if obj_id in self._widget_refs and attr_name in self._widget_refs[obj_id]:
            return self._widget_refs[obj_id][attr_name]
        
        # Fallback para getattr e armazenar no cache
        widget = getattr(obj, attr_name, default)
        if widget is not default:
            self.cache_widget(obj, attr_name, widget)
        
        return widget
    
    def cache_widget_list(self, pattern: str, widgets: List[Any]):
        """
        Armazena lista de widgets com padrão específico.
        
        Args:
            pattern: Padrão identificador da lista
            widgets: Lista de widgets
        """
        self._widget_lists[pattern] = widgets
    
    def get_widget_list(self, pattern: str) -> List[Any]:
        """
        Recupera lista de widgets por padrão.
        
        Args:
            pattern: Padrão identificador
            
        Returns:
            Lista de widgets
        """
        return self._widget_lists.get(pattern, [])
    
    def invalidate_object(self, obj: Any):
        """Remove todas as referências de um objeto do cache."""
        obj_id = id(obj)
        self._widget_refs.pop(obj_id, None)
    
    def clear_cache(self):
        """Limpa todo o cache."""
        self._widget_refs.clear()
        self._widget_lists.clear()


class OptimizedWidgetOperations:
    """Operações otimizadas para widgets com cache."""
    
    def __init__(self, widget_cache: WidgetCache):
        self.cache = widget_cache
    
    def clear_entries_optimized(self, dobras_ui: Any, w: int):
        """
        Versão otimizada de limpeza de entradas usando cache.
        
        Args:
            dobras_ui: Interface de dobras
            w: Número da coluna
        """
        # Gerar chave para cache de widgets desta operação
        cache_key = f"entries_{id(dobras_ui)}_{w}"
        
        # Tentar recuperar lista cached de widgets
        cached_widgets = self.cache.get_widget_list(cache_key)
        
        if not cached_widgets:
            # Primeira execução - construir cache
            widgets = []
            for i in range(1, dobras_ui.n):
                entry = self.cache.get_widget(dobras_ui, f'aba{i}_entry_{w}')
                if entry:
                    widgets.append(entry)
            
            # Armazenar no cache
            self.cache.cache_widget_list(cache_key, widgets)
            cached_widgets = widgets
        
        # Usar widgets cached - muito mais rápido que getattr repetitivo
        for entry in cached_widgets:
            if entry:
                entry.delete(0, 'end')  # Usar 'end' em vez de tk.END para evitar import
                entry.config(bg="white")
    
    def clear_labels_optimized(self, dobras_ui: Any, w: int):
        """
        Versão otimizada de limpeza de labels usando cache.
        
        Args:
            dobras_ui: Interface de dobras
            w: Número da coluna
        """
        # Cache para labels de medidas e metades
        cache_key_labels = f"labels_{id(dobras_ui)}_{w}"
        cached_labels = self.cache.get_widget_list(cache_key_labels)
        
        if not cached_labels:
            # Construir cache de labels
            labels = []
            for i in range(1, dobras_ui.n):
                for prefixo in ['medidadobra', 'metadedobra']:
                    label = self.cache.get_widget(dobras_ui, f'{prefixo}{i}_label_{w}')
                    if label:
                        labels.append(label)
            
            # Labels de blank
            for suffix in ['medida_blank_label', 'metade_blank_label']:
                label = self.cache.get_widget(dobras_ui, f'{suffix}_{w}')
                if label:
                    labels.append(label)
            
            self.cache.cache_widget_list(cache_key_labels, labels)
            cached_labels = labels
        
        # Limpar usando cache
        for label in cached_labels:
            if label:
                label.config(text="")
    
    def clear_header_widgets_optimized(self, cabecalho_ui: Any):
        """
        Versão otimizada de limpeza de widgets do cabeçalho.
        
        Args:
            cabecalho_ui: Interface do cabeçalho
        """
        cache_key = f"header_widgets_{id(cabecalho_ui)}"
        cached_operations = self.cache.get_widget_list(cache_key)
        
        if not cached_operations:
            # Construir cache de operações
            operations = []
            
            # Widgets de entrada para limpar
            entry_widgets = [
                'raio_interno_widget',
                'comprimento_widget', 
                'deducao_especifica_widget'
            ]
            
            for widget_name in entry_widgets:
                widget = self.cache.get_widget(cabecalho_ui, widget_name)
                if widget:
                    operations.append(('clear_entry', widget))
            
            # Widgets de combo para resetar
            combo_widgets = [
                ('material_widget', ''),
                ('espessura_widget', ''),
                ('canal_widget', '')
            ]
            
            for widget_name, default_value in combo_widgets:
                widget = self.cache.get_widget(cabecalho_ui, widget_name)
                if widget:
                    operations.append(('set_combo', widget, default_value))
            
            # Labels para resetar
            label_widgets = [
                ('fator_k_widget', ''),
                ('deducao_widget', ''),
                ('offset_widget', ''),
                ('observacoes_widget', ''),
                ('ton_m_widget', ''),
                ('aba_minima_widget', ''),
                ('z90_widget', '')
            ]
            
            for widget_name, text in label_widgets:
                widget = self.cache.get_widget(cabecalho_ui, widget_name)
                if widget:
                    operations.append(('set_label', widget, text))
            
            self.cache.cache_widget_list(cache_key, operations)
            cached_operations = operations
        
        # Executar operações cached
        for operation in cached_operations:
            op_type = operation[0]
            widget = operation[1]
            
            if op_type == 'clear_entry':
                widget.delete(0, 'end')
            elif op_type == 'set_combo':
                value = operation[2]
                widget.set(value)
                if hasattr(widget, 'configure'):
                    widget.configure(values=[])
            elif op_type == 'set_label':
                text = operation[2]
                widget.config(text=text)


# Instância global do cache de widgets
widget_cache = WidgetCache()
optimized_ops = OptimizedWidgetOperations(widget_cache)


def cache_widget_ref(obj: Any, attr_name: str, widget: Any):
    """Função conveniente para cache de widget."""
    widget_cache.cache_widget(obj, attr_name, widget)


def get_cached_widget(obj: Any, attr_name: str, default: Any = None) -> Any:
    """Função conveniente para recuperar widget cached."""
    return widget_cache.get_widget(obj, attr_name, default)


def clear_entries_fast(dobras_ui: Any, w: int):
    """Função otimizada para limpeza rápida de entradas."""
    optimized_ops.clear_entries_optimized(dobras_ui, w)


def clear_labels_fast(dobras_ui: Any, w: int):
    """Função otimizada para limpeza rápida de labels."""
    optimized_ops.clear_labels_optimized(dobras_ui, w)


def clear_header_fast(cabecalho_ui: Any):
    """Função otimizada para limpeza rápida do cabeçalho."""
    optimized_ops.clear_header_widgets_optimized(cabecalho_ui)
