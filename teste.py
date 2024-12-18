import tkinter as tk

root = tk.Tk()
root.title("Exemplo de Layout")

# Criando um Frame
frame = tk.Frame(root)
frame.grid(row=0, column=0, padx=10, pady=10)

# Adicionando widgets ao Frame
label = tk.Label(frame, text="Nome:")
label.grid(row=0, column=0, sticky="e")

entry = tk.Entry(frame)
entry.grid(row=0, column=1)

button = tk.Button(frame, text="Enviar")
button.grid(row=1, columnspan=2)

root.mainloop()