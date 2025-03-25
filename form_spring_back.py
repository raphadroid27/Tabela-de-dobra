import tkinter as tk
from tkinter import ttk
import globals as g
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Material

engine = create_engine('sqlite:///tabela_de_dobra.db')
session = sessionmaker(bind=engine)
session = session()

spring_back_form = tk.Tk()
spring_back_form.title("Cálculo de Spring Back")

frame = tk.Frame(spring_back_form)
frame.pack(pady=5, padx=5, fill='both', expand=True)

tk.Label(frame, text = "Material:").grid(row=0, column=0)
g.material_combobox = ttk.Combobox(frame, values = [session.query(Material)])
g.material_combobox.grid(row=1, column=0)

spring_back_form.mainloop()
