import tkinter as tk
import placeholder as ph

# Exemplo de uso
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Placeholder com Classe")

    placeholder_entry = ph.PlaceholderEntry(root, placeholder="Digite algo aqui...", width=20, justify="center")
    placeholder_entry.pack(pady=10)

    def print_input(event=None):
        print("Texto digitado:", placeholder_entry.get())

    # Vincula um evento à Entry encapsulada
    placeholder_entry.bind("<KeyRelease>", lambda event: print_input())

    root.mainloop()