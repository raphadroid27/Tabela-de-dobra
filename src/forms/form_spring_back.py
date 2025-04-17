import os
import tkinter as tk
from tkinter import ttk
from src.config import globals as g
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.models.material import Material  # Adjust the import path to match the actual location of Material

# Configuração do banco de dados


spring_back_form = tk.Tk()
spring_back_form.title("Cálculo de Spring Back")

frame = tk.Frame(spring_back_form)
frame.pack(pady=5, padx=5, fill='both', expand=True)

tk.Label(frame, text = "Material:").grid(row=0, column=0)
g.MAT_COMB = ttk.Combobox(frame, values = [session.query(Material)])
g.MAT_COMB.grid(row=1, column=0)

spring_back_form.mainloop()
