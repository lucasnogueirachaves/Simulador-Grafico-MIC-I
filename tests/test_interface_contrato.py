"""Smoke test sem janela real: verifica os contratos e atributos da GUI.

Não substitui executar a janela com CustomTkinter instalado e um servidor gráfico.
"""
import importlib
import sys
import types


def test_gui_instancia_e_executa_sem_widgets_ausentes(monkeypatch):
    modulo = types.ModuleType("customtkinter")

    class Widget:
        def __init__(self, *args, **kwargs):
            self.texto = ""
            self.propriedades = kwargs

        def __getattr__(self, nome):
            # Metodologia: somente API Tk compartilhada, atributos da app
            # continuam verificáveis e levantam AttributeError se ausentes.
            if nome in {"pack", "grid", "grid_columnconfigure", "grid_rowconfigure",
                        "title", "geometry", "minsize", "protocol", "destroy", "mainloop"}:
                return lambda *a, **kw: None
            raise AttributeError(nome)

        def get(self, *args):
            return self.texto

        def insert(self, index, texto):
            self.texto += texto

        def delete(self, *args):
            self.texto = ""

        def configure(self, **kwargs):
            self.propriedades.update(kwargs)

        def set(self, valor):
            self.valor = valor

        def after(self, ms, func):
            return "fake-task"

        def after_cancel(self, identificador):
            pass

    for nome in ("CTk", "CTkScrollableFrame", "CTkFrame", "CTkLabel", "CTkButton", "CTkTextbox", "CTkSlider"):
        setattr(modulo, nome, Widget)
    modulo.set_appearance_mode = lambda *a: None
    modulo.set_default_color_theme = lambda *a: None

    monkeypatch.setitem(sys.modules, "customtkinter", modulo)
    monkeypatch.delitem(sys.modules, "interface.interface", raising=False)
    app_mod = importlib.import_module("interface.interface")
    app = app_mod.Mic1SimulatorApp()
    assert app.cpu.memoria.memoria.ler(0) == 0x7005
    assert len(app.reg_labels) == 16
    assert len(app.cache_labels) == 2
    assert app.machine_code_box.texto.splitlines()[1].startswith("0001:")
    app.executar_passo()
    app.executar_ciclo()
    app.reiniciar()
    assert app.cpu.memoria.memoria.ler(0) == 0x7005
    app.iniciar_execucao()
    app.pausar_execucao()
    app._fechar()
    monkeypatch.delitem(sys.modules, "interface.interface", raising=False)
