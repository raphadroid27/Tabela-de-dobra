import tkinter as tk
from tkinter import messagebox
import globals as g

def authenticate():
    username = entry_username.get()
    password = entry_password.get()
    
    # Aqui você pode adicionar a lógica de autenticação
    if username == "admin" and password == "password":
        messagebox.showinfo("Login", "Autenticação bem-sucedida!")
    else:
        messagebox.showerror("Login", "Nome de usuário ou senha incorretos.")

# Configuração da janela principal
g.aut_form = tk.Toplevel()
g.aut_form.geometry("300x200")
g.aut_form.resizable(False, False)
g.aut_form.title("Formulário de Autenticação")

# Rótulos e campos de entrada
tk.Label(g.aut_form, text="Nome de usuário:").pack(pady=5)
entry_username = tk.Entry(g.aut_form)
entry_username.pack(pady=5)

label_password = tk.Label(g.aut_form, text="Senha:")
label_password.pack(pady=5)
entry_password = tk.Entry(g.aut_form, show="*")
entry_password.pack(pady=5)

# Botão de login
button_login = tk.Button(g.aut_form, text="Login", command=authenticate)
button_login.pack(pady=20)

# Iniciar o loop principal da interface gráfica
g.aut_form.mainloop()