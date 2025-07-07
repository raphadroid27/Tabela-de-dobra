"""
Módulo para gerenciar o estado dos widgets entre recriações da interface.
Sistema simplificado de cache para preservar valores de entrada do usuário.
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
                if widget is not None:
                    try:
                        if hasattr(widget, 'currentText'):
                            value = widget.currentText()
                        elif hasattr(widget, 'text'):
                            value = widget.text()
                        else:
                            value = ''
                        cabecalho_state[widget_name] = value
                        print(f"[STATE] Capturado {widget_name}: '{value}'")
                    except (AttributeError, TypeError) as e:
                        print(f"[STATE] Erro ao capturar {widget_name}: {e}")
                        cabecalho_state[widget_name] = ''

            self.widget_cache['cabecalho'] = cabecalho_state

            # Capturar valores das dobras
            dobras_state = {}
            if hasattr(g, 'VALORES_W') and hasattr(g, 'N'):
                for w in g.VALORES_W:
                    for i in range(1, g.N):
                        widget_name = f'aba{i}_entry_{w}'
                        widget = getattr(g, widget_name, None)
                        if widget is not None and hasattr(widget, 'text'):
                            try:
                                value = widget.text()
                                dobras_state[widget_name] = value
                                if value:  # Só mostrar se não estiver vazio
                                    print(
                                        f"[STATE] Capturado {widget_name}: '{value}'")
                            except (AttributeError, TypeError) as e:
                                print(
                                    f"[STATE] Erro ao capturar {widget_name}: {e}")
                                dobras_state[widget_name] = ''

            self.widget_cache['dobras'] = dobras_state
            print(
                f"[STATE] Estado capturado com sucesso. Widgets no cache: {len(self.widget_cache)}")

        except (AttributeError, TypeError) as e:
            print(f"[STATE] Erro ao capturar estado: {e}")

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
                    if widget is not None:
                        try:
                            if hasattr(widget, 'setCurrentText'):
                                # Para comboboxes, tentar primeiro setCurrentText
                                # Se falhar, tentar adicionar o item se não existir
                                try:
                                    widget.setCurrentText(value)
                                    # Verificar se foi definido corretamente
                                    if widget.currentText() != value:
                                        # Tentar encontrar item similar ou adicionar
                                        index = widget.findText(value)
                                        if index >= 0:
                                            widget.setCurrentIndex(index)
                                        else:
                                            # Adiciona item se não existir (combobox editável)
                                            if widget.isEditable():
                                                widget.addItem(value)
                                                widget.setCurrentText(value)
                                except (AttributeError, TypeError) as e:
                                    print(
                                        f"[STATE] Falha ao restaurar combobox {widget_name}: {e}")

                                print(
                                    f"[STATE] Restaurado {widget_name}: '{value}' "
                                    f"(combobox) -> atual: '{widget.currentText()}'"
                                )
                            elif hasattr(widget, 'setText'):
                                widget.setText(value)
                                print(
                                    f"[STATE] Restaurado {widget_name}: '{value}' (entry)")
                        except (AttributeError, TypeError) as e:
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
                    if widget is not None and hasattr(widget, 'setText'):
                        try:
                            widget.setText(value)
                            restored_count += 1
                            print(
                                f"[STATE] Restaurado {widget_name}: '{value}'")
                        except (AttributeError, TypeError) as e:
                            print(
                                f"[STATE] Erro ao restaurar {widget_name}: {e}")

                print(
                    f"[STATE] Restaurados {restored_count} widgets de dobras")

            print("[STATE] Restauração concluída")

        except (AttributeError, TypeError) as e:
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
