"""
Módulo para gerenciar o estado dos widgets entre recriações da interface.
Sistema robusto com tratamento de widgets deletados.
"""

import src.config.globals as g


class WidgetStateManager:
    """Gerenciador de estado dos widgets para preservar valores durante recriações da interface."""

    def __init__(self):
        self.widget_cache = {}
        self.is_enabled = True

    def enable(self):
        """Habilita o gerenciamento de estado."""
        self.is_enabled = True

    def disable(self):
        """Desabilita o gerenciamento de estado."""
        self.is_enabled = False

    def is_widget_valid(self, widget):
        """
        Verifica se um widget ainda é válido (não foi deletado).

        Args:
            widget: Widget a ser verificado

        Returns:
            bool: True se o widget é válido, False caso contrário
        """
        if widget is None:
            return False

        try:
            # Tenta acessar uma propriedade básica para verificar se o widget ainda existe
            widget.objectName()
            return True
        except RuntimeError:
            # Widget foi deletado pelo Qt
            return False

    def safe_get_widget_value(self, widget):
        """
        Obtém o valor de um widget de forma segura.

        Args:
            widget: Widget do qual obter o valor

        Returns:
            str: Valor do widget ou string vazia se houver erro
        """
        if not self.is_widget_valid(widget):
            return ''

        try:
            if hasattr(widget, 'currentText'):
                return widget.currentText()
            elif hasattr(widget, 'text'):
                return widget.text()
            else:
                return ''
        except RuntimeError:
            # Widget foi deletado durante a operação
            return ''

    def capture_current_state(self):
        """Captura o estado atual de todos os widgets relevantes."""
        if not self.is_enabled:
            return

        try:
            # Capturar valores do cabeçalho
            cabecalho_state = {}
            widget_names = ['MAT_COMB', 'ESP_COMB', 'CANAL_COMB',
                            'COMPR_ENTRY', 'RI_ENTRY', 'DED_ESPEC_ENTRY']

            for widget_name in widget_names:
                widget = getattr(g, widget_name, None)
                if self.is_widget_valid(widget):
                    try:
                        value = self.safe_get_widget_value(widget)
                        cabecalho_state[widget_name] = value
                        if value:  # Só mostrar se não estiver vazio
                            print(
                                f"[STATE] Capturado {widget_name}: '{value}'")
                    except (AttributeError, TypeError, RuntimeError) as e:
                        print(f"[STATE] Erro ao capturar {widget_name}: {e}")
                        cabecalho_state[widget_name] = ''
                else:
                    cabecalho_state[widget_name] = ''

            self.widget_cache['cabecalho'] = cabecalho_state

            # Capturar valores das dobras
            dobras_state = {}
            if hasattr(g, 'VALORES_W') and hasattr(g, 'N'):
                for w in g.VALORES_W:
                    for i in range(1, g.N):
                        widget_name = f'aba{i}_entry_{w}'
                        widget = getattr(g, widget_name, None)
                        if self.is_widget_valid(widget):
                            try:
                                value = self.safe_get_widget_value(widget)
                                dobras_state[widget_name] = value
                                if value:  # Só mostrar se não estiver vazio
                                    print(
                                        f"[STATE] Capturado {widget_name}: '{value}'")
                            except (AttributeError, TypeError, RuntimeError) as e:
                                print(
                                    f"[STATE] Erro ao capturar {widget_name}: {e}")
                                dobras_state[widget_name] = ''
                        else:
                            dobras_state[widget_name] = ''

            self.widget_cache['dobras'] = dobras_state
            print(
                f"[STATE] Estado capturado com sucesso. Widgets no cache: {len(self.widget_cache)}")

        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao capturar estado: {e}")

    def safe_restore_combobox(self, widget, value):
        """
        Restaura valor de combobox de forma segura.

        Args:
            widget: Widget combobox
            value: Valor a ser restaurado

        Returns:
            bool: True se restaurou com sucesso
        """
        if not self.is_widget_valid(widget) or not value:
            return False

        try:
            if hasattr(widget, 'setCurrentText'):
                widget.setCurrentText(value)

                # Verificar se foi definido corretamente
                if widget.currentText() == value:
                    return True

                # Tentar encontrar item similar
                index = widget.findText(value)
                if index >= 0:
                    widget.setCurrentIndex(index)
                    return True

                # Adicionar item se não existir (combobox editável)
                if hasattr(widget, 'isEditable') and widget.isEditable():
                    widget.addItem(value)
                    widget.setCurrentText(value)
                    return True

            return False

        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao restaurar combobox: {e}")
            return False

    def safe_restore_entry(self, widget, value):
        """
        Restaura valor de entry de forma segura.

        Args:
            widget: Widget entry
            value: Valor a ser restaurado

        Returns:
            bool: True se restaurou com sucesso
        """
        if not self.is_widget_valid(widget) or not value:
            return False

        try:
            if hasattr(widget, 'setText'):
                widget.setText(value)
                return True
            return False

        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao restaurar entry: {e}")
            return False

    def restore_widget_state(self):
        """Restaura o estado dos widgets a partir do cache."""
        if not self.is_enabled or not self.widget_cache:
            print("[STATE] Cache vazio ou desabilitado - nada para restaurar")
            return

        try:
            print("[STATE] Restaurando estado dos widgets...")

            # Restaurar cabeçalho
            if 'cabecalho' in self.widget_cache:
                cabecalho_state = self.widget_cache['cabecalho']
                for widget_name, value in cabecalho_state.items():
                    if not value:  # Pular valores vazios
                        continue

                    widget = getattr(g, widget_name, None)
                    if self.is_widget_valid(widget):
                        try:
                            if hasattr(widget, 'setCurrentText'):
                                success = self.safe_restore_combobox(
                                    widget, value)
                                if success:
                                    print(
                                        f"[STATE] Restaurado {widget_name}: '{value}' (combobox)")
                            elif hasattr(widget, 'setText'):
                                success = self.safe_restore_entry(
                                    widget, value)
                                if success:
                                    print(
                                        f"[STATE] Restaurado {widget_name}: '{value}' (entry)")
                        except (AttributeError, TypeError, RuntimeError) as e:
                            print(
                                f"[STATE] Erro ao restaurar {widget_name}: {e}")

            # Restaurar dobras
            if 'dobras' in self.widget_cache:
                dobras_state = self.widget_cache['dobras']
                restored_count = 0

                for widget_name, value in dobras_state.items():
                    if not value:  # Pular valores vazios
                        continue

                    widget = getattr(g, widget_name, None)
                    if self.is_widget_valid(widget):
                        success = self.safe_restore_entry(widget, value)
                        if success:
                            restored_count += 1
                            print(
                                f"[STATE] Restaurado {widget_name}: '{value}'")

                print(
                    f"[STATE] Restaurados {restored_count} widgets de dobras")

            print("[STATE] Restauração concluída")

        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao restaurar estado: {e}")

    def clear_cache(self):
        """Limpa o cache de widgets."""
        self.widget_cache.clear()
        print("[STATE] Cache limpo")

    def get_cache_info(self):
        """Retorna informações sobre o cache atual."""
        cabecalho_count = len(self.widget_cache.get('cabecalho', {}))
        dobras_count = len(self.widget_cache.get('dobras', {}))
        return f"Cache: {cabecalho_count} widgets de cabeçalho, {dobras_count} widgets de dobras"


# Instância global do gerenciador de estado
widget_state_manager = WidgetStateManager()
