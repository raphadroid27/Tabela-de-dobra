import tkinter as tk
from tkinter import ttk

def main():
    root = tk.Tk()
    root.title("Exemplo de Estilo com Tkinter")
    root.geometry("400x300")

    style = ttk.Style()
    style.configure("TButton", font=("Helvetica", 12), padding=10)
    style.configure("TLabel", font=("Helvetica", 14), background="lightblue")

    label = ttk.Label(root, text="Olá, Tkinter!", style="TLabel")
    label.pack(pady=20)

    button = ttk.Button(root, text="Clique Aqui", style="TButton")
    button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()