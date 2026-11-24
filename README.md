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

## Executar a versão corrigida

Requisitos: Python 3.10+ e interface gráfica disponível (Tk/Tkinter).

Crie um ambiente virtual isolado na raiz do projeto:

```bash
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

Instale as dependências e execute:

```bash
python -m pip install -r requirements.txt
python -m interface.interface
```

**Execute os comandos a partir da pasta raiz do projeto.** Na tela, use **Montar e carregar** para transferir o programa MAC-1 à RAM. Você pode avançar **Subciclo** a subciclo, concluir uma **Microinstrução**, **Executar** continuamente, **Pausar** e ajustar o intervalo entre subciclos pelo controle deslizante. **Reset** reinicia registradores e contadores sem apagar a RAM. **Montar e carregar** substitui o programa e a RAM.

Para testar:

```bash
python -m pytest -q
```

Os testes de interface usam objetos gráficos simulados para validar as conexões; é importante testar visualmente com CustomTkinter instalado e ambiente com tela.

## Decisões de implementação

- O microprograma distribuído usa os endereços de controle 0 e 1 na busca da macroinstrução; apenas os comandos `RD` desses endereços são enviados à cache de instruções. Outros `RD` usam a cache de dados. Se o microprograma for substituído, essa classificação deverá ser revista.
- Escritas fazem uma única alteração na RAM (*write-through*) e atualizam linhas já presentes nas duas caches; nenhuma linha nova é alocada em uma escrita.
- `carregar_programa()` valida as palavras, substitui toda a RAM, invalida as caches e reinicia a execução.
- `get_state()` retorna cópias dos dados de memória e dos sinais para a interface não modificar acidentalmente os componentes.
- A memória ainda responde imediatamente a `RD` e `WR`. Os quatro subciclos são etapas de simulação didática, não tempos elétricos reais de hardware.
- O encerramento de programa é estimado pela posição do PC ao retornar ao endereço 0 do microprograma; não corresponde a um opcode HALT nativo.
