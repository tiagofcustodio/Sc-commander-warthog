# 🚀 Star Citizen — Warthog Commander PRO (v5.4 UEE MIL-GLASS)

> **☕ If you like this project, buy me a coffee:** [https://paypal.me/tcustodio](https://paypal.me/tcustodio)
> **📦 GitHub Repository:** [https://github.com/tiagofcustodio/Sc-commander-warthog](https://github.com/tiagofcustodio/Sc-commander-warthog)

Centro de Comando Tático, motor DirectInput inteligente, estúdio visual de mapeamento e reparador automático de `actionmaps.xml` para **Star Citizen 4.x**, com suporte **Multi-HOTAS**:
* **Thrustmaster:** HOTAS Warthog (A-10C 19B + Dual Throttle 32B + 5 LEDs HID), T.16000M FCS + TWCS Throttle, TCA Officer Pack Airbus, T.Flight HOTAS (X / 4 / One), Cougar & Viper TQS.
* **Saitek / Logitech G:** X56 Rhino HOTAS (Stick 17B + Throttle 32B).

### ✨ Funcionalidades Principais
* **Interface Star Citizen UEE / Aegis Military-Grade Glass** com cortes chanfrados a 45° e alta legibilidade.
* **Mapa Visual Interativo dos 2 Joysticks** com troca automática das imagens ao detetar o hardware USB ligado e **Mira HUD Target-Lock** ao passar o rato ou premir botões físicos.
* **Editor de Teclas & Botões do Rato (`MOUSE1`–`MOUSE5`, `MWHEEL_UP/DOWN`)** com captura interativa instantânea.
* **Ação Dupla por Botão (*Toque Curto vs Pressão Longa / Hold*)** configurável em milissegundos.
* **Estúdio de Macros Multi-Passo** (ex: *Aterragem Completa*, *Pronto para Combate*, *Preparação Quantum*).
* **Computador de Bordo por Voz (*Ship AI Voice*)** em Inglês Aviónica (Aegis/Anvil) ou Português Tático.
* **Auto-Doctor XML** + **Atualização Automática** com backup ZIP seguro preservando `config.json`.

---

## 🔍 Porque é que o Joystick funcionava mas os Thrusters (Manete) não?

A análise direta aos teus ficheiros do Star Citizen (`C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\user\client\0\Profiles\default\actionmaps.xml` e `layout_CJ080621.xml`) e ao comportamento do hardware Thrustmaster Warthog revelou **4 causas exatas**:

1. **Conflito Crítico nas Duas Alavancas da Manete (`js2_rotz` vs `js2_z`)**:
   - Na Manete Dupla do Warthog, a **Alavanca Direita (Principal)** é o eixo `js2_rotz` (`Rz`) e a **Alavanca Esquerda** é o eixo `js2_z` (`Z`). Quando ambas estão travadas juntas pelo pino metálico, mexer a manete move **ambos os eixos em simultâneo**.
   - No teu `actionmaps.xml`, o eixo `js2_rotz` (Alavanca Direita!) estava mapeado para `v_ifcs_speed_limiter_rel` (**Limitador de Velocidade Relativo**), enquanto `js2_z` estava em `v_strafe_longitudinal` com uma curva extrema `exponent="2.9000001"`!
   - **Resultado**: Ao mover a manete, a Alavanca Direita reduzia o Limitador de Velocidade para `0 m/s` (travando a nave), ou se a Alavanca Esquerda ficasse estacionada no detentor `OFF`, mexer a Alavanca Direita apenas mexia a barra do limitador sem dar qualquer potência aos propulsores!
2. **Bloqueio dos Detentores Físicos de Idle Cutoff (Botões 29 e 30)**:
   - Puxar as manetes para trás do batente físico `OFF` mantém os **Botões 29 e 30** continuamente premidos (`ON`). Se ambos os manípulos saírem ou entrarem em `OFF` juntos, sem *debounce*, o comando `I` (Energia dos Propulsores) dispara duas vezes seguidas (ligando e desligando os motores imediatamente).
3. **Slots Fantasma na API `winmm` do Windows (`Controller (Gamepad)`)**:
   - O teu sistema tem um `Controller (Gamepad)` registado no Windows juntamente com o Manche (`PID_0402`) e a Manete (`PID_0404`). O leitor antigo consultava apenas as capacidades de registo (`joyGetDevCapsW`) sem verificar se o slot estava fisicamente ativo via `joyGetPosEx`, podendo ligar o leitor da manete a um slot inativo.
4. **Falta de `v_pitch` (`js1_y`) e `spaceship_weapons` no `actionmaps.xml`**:
   - O eixo Y do manche (`v_pitch`) e os grupos de disparo 1 e 2 (`v_attack1_group1`, `v_attack1_group2`) tinham desaparecido do `actionmaps.xml`.

---

## 🛠️ O Que Foi Corrigido e Melhorado

- **Reparação Automática dos Thrusters e Eixos (`actionmaps_fixer.py`)**:
  - Remove `js2_rotz` de `v_ifcs_speed_limiter_rel`.
  - Mapeia **ambas as alavancas da manete** para propulsão (`js2_z` → `v_strafe_longitudinal` e `js2_rotz` → `v_throttle_abs`) com `invert="1"` e `exponent="1.0"` (resposta linear imediata).
  - Move o **Limitador de Velocidade Absoluto** (`v_speed_range_abs`) e a **Potência do Laser de Mineração** (`v_mining_throttle`) para a **Roda Cinzenta de Fricção Central (`js2_slider1`)**.
  - Mapeia o **Mini-Stick Analógico (Slew Control `js2_x` / `js2_y`)** para **Strafe Lateral (Esquerda/Direita)** e **Strafe Vertical (Cima/Baixo)**.
- **Deteção de Hardware Física + Registo OEM (`dinput_reader.py`)**:
  - Valida cada slot com `joyGetPosEx` (ignorando slots fantasma e Gamepads), lê o `OEMName` via Registo do Windows (`VID_044F&PID_0402` e `VID_044F&PID_0404`), monitoriza os **5 eixos da manete em tempo real** e deteta o estado dos detentores **Idle Cutoff (Botões 29 e 30)**.
- **Debounce Inteligente de 350ms no Idle Cutoff (`switch_engine.py`)**:
  - Quando moves as duas alavancas unidas para fora ou para dentro do batente `OFF`, os botões 29 e 30 acionam com milissegundos de diferença — o motor aplica um *debounce* de `350ms` para enviar apenas **1 único pulso `I`**, evitando desligar os motores ao tirá-los de `OFF`.
- **Elevação Automática de Administrador (`run.bat`)**:
  - Como o teu Star Citizen está instalado em `C:\Program Files\Roberts Space Industries\StarCitizen\LIVE`, o `run.bat` pede automaticamente permissões de Administrador (UAC) e repara o `actionmaps.xml` logo no arranque!

---

## 🕹️ Mapa Completo de Todas as Teclas, Hats e Eixos

### 1. Manche A-10C (`js1` — 19 Botões + POV Hat + 2 Eixos)

| Controlo Físico | Input SC | Ação Normal no Star Citizen | Camada Shift (`S4 Pinky Lever` premido) |
| :--- | :--- | :--- | :--- |
| **Eixo X** | `js1_x` | **Roll** (Rolamento da Nave / Yaw na Torre) | — |
| **Eixo Y** | `js1_y` | **Pitch** (Arfagem da Nave / Pitch na Torre) | — |
| **POV1 Hat (Trim Hat)** | `js1_hat1_up/right/left/down` | **Triângulo de Energia**: `Cima`=Propulsores (`F6`), `Dir`=Escudos (`F7`), `Esq`=Armas (`F5`), `Baixo`=Reset (`F8`) | — |
| **Botão 1 (TG1 — Gatilho 1)** | `js1_button1` | Disparar Armas Grupo 1 / Laser Mineração / Scan | — |
| **Botão 5 (TG2 — Gatilho 2)** | `js1_button5` | Disparar Armas Grupo 2 (Fogo Total) | — |
| **Botão 2 (S2 — Weapon Release)** | `js1_button2` | Travar / Disparar Míssil / Alternar Modo Laser | **Alt+J** (Ejetar Carga Volátil) |
| **Botão 3 (S3 — Nosewheel Steering)** | `js1_button3` | Alternar Modo Gimbal / Igualar Velocidade ao Alvo | — |
| **Botão 4 (S4 — Pinky Lever)** | `js1_button4` | **MODIFICADOR SHIFT GLOBAL** + Alternar Decoupled (`Alt+C`) | — |
| **Botão 6 (S1 — Master Mode)** | `js1_button6` | Segurar: Alternar Master Mode **SCM ↔ NAV** (`B`) | **K** (Alternar VTOL) |
| **Botões 7–10 (TMS Hat)** | `js1_button7..10` | `7 Cima`: Lock Alvo à Frente · `8 Dir`: Próximo Hostil · `9 Baixo`: Ameaça Principal · `10 Esq`: Hostil Anterior / Pin | `7`: Sub-alvo Fwd (`R`) · `9`: Reset Sub-alvo · `10`: Pin (`1`) |
| **Botões 11–14 (DMS Hat)** | `js1_button11..14` | `11 Cima`: Radar Ping (`Tab`) · `12 Dir`: Aumentar Ângulo Ping / Alvo · `13 Baixo`: Reset Escudos (`Num5`) · `14 Esq`: Diminuir Ângulo Ping | Ajustes de Foco de Radar |
| **Botões 15–19 (CMS Hat + Push)** | `js1_button15..19` | `15 Cima`: Noise Field (`J`) · `16 Dir`: +Burst Decoy / Próximo Míssil (`G`) · `17 Baixo`: Lançar Decoy (`H`) · `18 Esq`: -Burst Decoy · `19 Push`: Salva Pânico / +Mísseis | — |

### 2. Manete Dupla A-10C (`js2` — 32 Botões + Coolie Hat + 5 Eixos)

| Controlo Físico | Input SC | Função no Star Citizen (Nativo XML + Motor de Pulsos) |
| :--- | :--- | :--- |
| **Alavanca Esquerda (Eixo Z)** | `js2_z` | **Propulsão Longitudinal (Avançar / Throttle Principal)** (`invert="1"`, linear) |
| **Alavanca Direita (Eixo Rz)** | `js2_rotz` | **Throttle Absoluto Sincronizado** (Funciona ligada ou independente da esquerda!) |
| **Roda Cinzenta Central (Slider 1)** | `js2_slider1` | **Limitador de Velocidade Absoluto** + **Potência do Laser de Mineração** |
| **Mini-Stick Slew X / Y** | `js2_x` / `js2_y` | **Strafe Horizontal (Esquerda/Direita)** e **Strafe Vertical (Cima/Baixo)** |
| **Coolie Hat (POV1)** | `js2_hat1_*` | **Guiada (Yaw Esq/Dir)** + **Strafe Vertical Rápido (Cima/Baixo)** |
| **Botão 1 (Slew Push)** | `js2_button1` | Igualar Velocidade ao Alvo / Modo Interação (`F`) |
| **Botões 2–5 (MIC Switch + Push)** | `js2_button2..5` | `2 Push`: Push-to-Talk VOIP (`Num+`) · `3 Cima`: Scan (`V`) · `4 Dir`: Câmara 3ª Pessoa (`F4`) · `5 Baixo`: Mineração/Salvage (`M`) |
| **Botões 6 (Esq) + 1 (Stick)** | `js2_button6` | Olhar Livre no Cockpit (Freelook `Z`) / Travão em Torres |
| **Botões 7–8 (Speedbrake)** | `js2_button7..8` | `7 Trás (Mola)`: **Space Brake (`X`)** · `8 Frente (Fixo)`: **Cruise Control (`C`)** |
| **Botões 9–10 (Boat Switch)** | `js2_button9..10` | `9 Frente`: Master Mode / Quantum (`B`) · `10 Trás`: Boost / Regressar SCM (`B`) |
| **Botões 11–12 (China Hat)** | `js2_button11..12` | `11 Frente (Vermelho)`: **Boost / Afterburner (`LShift`)** · `12 Trás`: **Inverter Propulsão / Recuar (`S`)** |
| **Botões 13–14 (Pinky Switch)** | `js2_button13..14` | `13 Frente`: Faróis Exteriores (`L`) · `Centro`: Desligar Faróis · `14 Trás`: Luzes da Cabine / Bombing |
| **Botão 15 (Left Throttle Button)** | `js2_button15` | **Flight Ready (`Alt+R`)** / Autoland (`N` em aterragem) |
| **Botões 16–17 (EAC ARM / OFF)** | `js2_button16..17` | `16 ARM`: **Engrenar Voo / Ligar Energia (`U`)** · `17 OFF`: ** acoplamento / Desligar Energia (`U`)** |
| **Botões 18–19 (RDR ALTM)** | `js2_button18..19` | `18 NRM`: **Levantar Trem de Aterragem (`N`)** · `19 DIS`: **Baixar Trem de Aterragem (`N`)** |
| **Botão 20 (APU START / OFF)** | `js2_button20` | `START`: **Flight Ready (`Alt+R`)** · `OFF`: **Desligar Tudo (`U`)** |
| **Botão 21 (LASTE Autopilot Push)** | `js2_button21` | **Chamar ATC (Aterragem / Descolagem `Alt+N`)** + Alternar Escudos (`O`) |
| **Botões 22–23 (ENG OPER Left)** | `js2_button22..23` | `22 IGN`: Energia Propulsores (`I`) · `Centro`: Propulsores ON · `23 MOTOR`: Cortar Propulsores OFF (`I`) |
| **Botões 24–25 (ENG OPER Right)** | `js2_button24..25` | `24 IGN`: Energia Armas (`P`) · `Centro`: Armas ON · `25 MOTOR`: Cortar Armas OFF (`P`) |
| **Botões 26 (FLAP U) / 27–28 (LASTE)** | `js2_button26..28` | `PATH`: **Abrir Todas as Portas (`Alt+K`)** · `ALT/HDG`: **Fechar Portas (`Alt+O`)** · `ALT`: **Trancar Portas (`Alt+L`)** |
| **Botões 29–30 (Idle Cutoff Esq/Dir)** | `js2_button29..30` | **Corte Físico de Motores (`I`) com Debounce de 350ms** (não bloqueia eixos no XML!) |
| **Botões 31–32 (ENG FUEL NORM)** | `js2_button31..32` | `31 Left`: **Limpar Visor (`Alt+X`)** · `32 Right`: **Ejetar (`Alt+Y` / Buzina Terrestre)** |

---

## ▶️ Como Executar

1. Faz duplo clique em **`run.bat`** (o script pede automaticamente permissão de **Administrador** para poder reparar o `actionmaps.xml` dentro de `C:\Program Files\Roberts Space Industries\StarCitizen\LIVE`).
2. O painel **Warthog Commander PRO** abre e:
   - Repara automaticamente o teu `actionmaps.xml` ativo.
   - Instala o perfil completo `layout_warthog_sc_fixed.xml` na pasta `controls\mappings` do Star Citizen.
   - Mostra em tempo real as barras dos eixos **Z (Manete Esq)**, **Rz (Manete Dir)** e **Slider 1 (Limitador)** e avisa se as manetes estiverem presas no detentor físico **Idle Cutoff OFF**.
