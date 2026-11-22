import customtkinter as ctk
from montador.montador import checar_erros, leitor, montador, passagens


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Mic1SimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Simulador MIC-1 - Arquitetura de Computadores")
        self.geometry("1350 = 850" if False else "1350x850")

        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        
        self.left_frame = ctk.CTkFrame(self, width=360, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
    
        self.label_editor = ctk.CTkLabel(self.left_frame, text="Código / Montador MIC-1", font=("Arial", 13, "bold"))
        self.label_editor.pack(padx=15, pady=(15, 5), anchor="w")

        self.text_box = ctk.CTkTextbox(self.left_frame, height=200, width=330, font=("Consolas", 11))
        self.text_box.pack(padx=15, pady=5)
        self.text_box.insert("0.0", "# Escreva seu código aqui\nLOAD SP\nPUSH 5\nADD\nSTORE TOS")

        
        self.label_机器 = ctk.CTkLabel(self.left_frame, text="CÓDIGO DE MÁQUINA", font=("Arial", 13, "bold"))
        self.label_机器.pack(padx=15, pady=(10, 5), anchor="w")

        self.machine_code_box = ctk.CTkTextbox(self.left_frame, height=140, width=330, font=("Consolas", 11), fg_color="#1a1a1a")
        self.machine_code_box.pack(padx=15, pady=5)
        self.machine_code_box.insert("0.0", "0000  10000393  LOAD SP\n0004  0063a023  PUSH 5\n0008  0003a403  ADD\n000C  0003a503  STORE TOS")
        self.machine_code_box.configure(state="disabled")

        
        self.btn_passo = ctk.CTkButton(self.left_frame, text="▶  Passo (Fase)", fg_color="#1f538d", hover_color="#143d6b", height=38, font=("Arial", 12, "bold"), command=self.executar_passo)
        self.btn_passo.pack(padx=15, pady=(15, 8), fill="x")

        self.btn_reiniciar = ctk.CTkButton(self.left_frame, text="⟳  Reiniciar", fg_color="#a83232", hover_color="#7a2424", height=32, font=("Arial", 12, "bold"), command=self.reiniciar)
        self.btn_reiniciar.pack(padx=15, pady=5, fill="x")

        
        self.stats_frame = ctk.CTkFrame(self.left_frame, fg_color="#1a1a1a", corner_radius=6)
        self.stats_frame.pack(padx=15, pady=(15, 15), fill="x")
        
        self.label_stats = ctk.CTkLabel(self.stats_frame, text="Ciclos: 0  |  Instruções: 0", font=("Consolas", 11, "bold"), text_color="#00ffcc")
        self.label_stats.pack(padx=10, pady=8)

        
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)

        
        self.reg_container = ctk.CTkFrame(self.right_frame)
        self.reg_container.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        self.reg_container.grid_columnconfigure(0, weight=1)

        self.label_regs = ctk.CTkLabel(self.reg_container, text="REGISTRADORES DO MIC-1", font=("Arial", 13, "bold"))
        self.label_regs.pack(padx=15, pady=(10, 5), anchor="w")

        self.regs_grid_frame = ctk.CTkFrame(self.reg_container, fg_color="transparent")
        self.regs_grid_frame.pack(padx=15, pady=(0, 10), fill="x")
        self.reg_labels = {}
        self.atualizar_interface_regs()

        
        self.cache_container = ctk.CTkFrame(self.right_frame)
        self.cache_container.grid(row=1, column=0, sticky="nsew")
        self.cache_container.grid_columnconfigure(0, weight=1)
        self.cache_container.grid_rowconfigure(1, weight=1)

        self.label_cache = ctk.CTkLabel(self.cache_container, text="MEMÓRIA PRINCIPAL / CACHE (MAPEAMENTO DIRETO)", font=("Arial", 13, "bold"))
        self.label_cache.pack(padx=15, pady=(10, 5), anchor="w")

        self.cache_grid_frame = ctk.CTkFrame(self.cache_container, fg_color="transparent")
        self.cache_grid_frame.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        
        self.atualizar_interface_cache()

    def atualizar_interface_regs(self):
        for widget in self.regs_grid_frame.winfo_children():
            widget.destroy()

        regs = self.cpu.get_registradores()
        col = 0
        row = 0
        for nome, valor in regs.items():
            lbl = ctk.CTkLabel(
                self.regs_grid_frame, 
                text=f"{nome}: {hex(valor) if isinstance(valor, int) else valor}", 
                font=("Consolas", 12, "bold"), 
                fg_color="#262626", 
                corner_radius=6, 
                height=35
            )
            lbl.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self.regs_grid_frame.grid_columnconfigure(col, weight=1)
            self.reg_labels[nome] = lbl
            
            col += 1
            if col > 2: 
                col = 0
                row += 1

    def atualizar_interface_cache(self):
        headers = ["Índice (#)", "Bit V (Validade)", "Tag", "Bloco / Palavras de Dados"]
        col_weights = [1, 1, 2, 4]

        for col_idx, h_text in enumerate(headers):
            lbl_h = ctk.CTkLabel(self.cache_grid_frame, text=h_text, font=("Arial", 11, "bold"), fg_color="#1f538d", corner_radius=4, height=30)
            lbl_h.grid(row=0, column=col_idx, padx=4, pady=4, sticky="nsew")
            self.cache_grid_frame.grid_columnconfigure(col_idx, weight=col_weights[col_idx])

        for i in range(8):
            lbl_idx = ctk.CTkLabel(self.cache_grid_frame, text=f"[{i}]", font=("Consolas", 11), fg_color="#262626", height=28)
            lbl_idx.grid(row=i+1, column=0, padx=4, pady=2, sticky="nsew")

            lbl_v = ctk.CTkLabel(self.cache_grid_frame, text="0", font=("Consolas", 11), fg_color="#262626", height=28)
            lbl_v.grid(row=i+1, column=1, padx=4, pady=2, sticky="nsew")

            lbl_tag = ctk.CTkLabel(self.cache_grid_frame, text="---", font=("Consolas", 11), fg_color="#262626", height=28)
            lbl_tag.grid(row=i+1, column=2, padx=4, pady=2, sticky="nsew")

            lbl_data = ctk.CTkLabel(self.cache_grid_frame, text="0x00000000", font=("Consolas", 11), fg_color="#262626", height=28)
            lbl_data.grid(row=i+1, column=3, padx=4, pady=2, sticky="nsew")

    def executar_passo(self):
        self.cpu.passo()
        self.atualizar_interface_regs()
        self.label_stats.configure(text=f"Ciclos: {self.cpu.ciclos}  |  Instruções: {self.cpu.instrucoes_executadas}")

    def reiniciar(self):
        self.cpu.reiniciar()
        self.atualizar_interface_regs()
        self.label_stats.configure(text="Ciclos: 0  |  Instruções: 0")

if __name__ == "__main__":
    app = Mic1SimulatorApp()
    app.mainloop()