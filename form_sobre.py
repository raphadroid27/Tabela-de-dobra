import tkinter as tk
import webbrowser
import globals as g

def main(root_app):
    g.sobre_form = tk.Toplevel()
    g.sobre_form.title("Sobre")
    g.sobre_form.geometry("300x210")
    g.sobre_form.resizable(False, False)
    g.sobre_form.attributes("-topmost", True)

    # Posicionar a janela nova_deducao em relação à janela principal
    g.sobre_form.update_idletasks() 
    x = root_app.winfo_x() + ((root_app.winfo_width() - g.sobre_form.winfo_width()) // 2)
    y = root_app.winfo_y() + ((root_app.winfo_height() - g.sobre_form.winfo_height()) // 2)
    g.sobre_form.geometry(f"+{x}+{y}")

    label_titulo = tk.Label(g.sobre_form, text="Tabela de Dobra", font=("Arial", 16, "bold"))
    label_titulo.pack(pady=10)

    label_versao = tk.Label(g.sobre_form, text="Versão: 0.1.0-beta", font=("Arial", 12))
    label_versao.pack(pady=5)

    label_autor = tk.Label(g.sobre_form, text="Autor: raphadroid27", font=("Arial", 12))
    label_autor.pack(pady=5)

    label_descricao = tk.Label(g.sobre_form, text="Aplicativo para cálculo de dobras.", font=("Arial", 12))
    label_descricao.pack(pady=10)

    def abrir_github():
        webbrowser.open("https://github.com/raphadroid27/Tabela-de-dobra")

    link_github = tk.Label(g.sobre_form, text="GitHub: raphadroid27/Tabela-de-dobra", font=("Arial", 12), fg="blue", cursor="hand2")
    link_github.pack(pady=5)
    link_github.bind("<Button-1>", lambda e: abrir_github())

    g.sobre_form.mainloop()

if __name__ == "__main__":
    main(None)