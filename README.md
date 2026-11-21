# Simulador Gráfico MIC-1

Ferramenta de simulação da microarquitetura do processador **MIC-1** (Tanenbaum), desenvolvida como projeto da disciplina **Arquitetura de Computadores** 

O simulador executa programas ciclo a ciclo (4 subciclos por ciclo) e permite acompanhar o datapath, a unidade de controle e as caches de instruções e de dados.

## Estrutura

```
Simulador-Grafico-MIC-I/
├── assets/
│   └── microprograma.txt     # microprograma (79 microinstruções de 32 bits)
├── componentes/              # núcleo do simulador (sem dependência de interface)
│   ├── cpu.py                # CPU: executa os subciclos e expõe o estado
│   ├── controle/             # memória de controle, MPC, MIR, Mmux
│   ├── memoria/              # memória principal, caches e controlador de memória
│   └── via_de_dados/         # registradores, ULA, deslocador, latches, Amux, MAR, MBR
├── montador/                 # montador (assembly para código de máquina)
├── interface/                # interface gráfica (Tkinter)
└── README.md
```