"""
Gerador de Diagrama Ultra-HD e Modelos 3D (.STL / .SVG / Preview 3D)
para a Manete Dupla (Dual Throttle) do Thrustmaster HOTAS Warthog no Star Citizen.

Produz:
1. warthog_manete_dupla_sc_mapa.png:
   Diagrama Oficial Ultra-HD (3368 x 2381 px) da Manete Dupla (Base + Punhos)
   usando as imagens recortadas oficiais da Thrustmaster e linhas de chamada exatas
   com os nomes de todos os 32 botões, eixos, Coolie Hat e 5 LEDs em Português.
2. warthog_throttle_placa_base_3d.stl:
   Placa física 3D (146 x 124 x 2.8 mm) para impressora 3D com furos reais para os
   interruptores da base da Manete Dupla, 5 LEDs e rasgo das manetes + letras 3D em
   alto-relevo (+0.8 mm) para troca de cor de filamento na camada 2.0 mm.
3. warthog_manete_dupla_quadro_3d.stl:
   Quadro/Placa 3D completa (210 x 148 x 2.4 mm) da Manete Dupla + Punhos com todas
   as legendas dos botões em alto-relevo 3D para colocar na secretária / cockpit.
4. warthog_throttle_placa_3d_preview.png:
   Renderização 3D sombreada das placas 3D geradas.
5. warthog_throttle_placa_1para1.svg:
   Molde vetorial 1:1 em milímetros para corte a laser ou impressão em papel/vinil.
"""

from __future__ import annotations

import io
import os
import re
import struct
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

TARGET_THROTTLE_PDF = Path(
    r"C:\Program Files (x86)\Thrustmaster\TARGET\Resources\warthog_throttle.pdf"
)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf"]
        if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"]
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_pdf_predictor15_as_png(width: int, height: int, flate_bytes: bytes) -> Image.Image:
    """Converte um stream FlateDecode (/Predictor 15, Grayscale 8-bit) num PNG válido em memória."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", flate_bytes)
        + _chunk(b"IEND", b"")
    )
    return Image.open(io.BytesIO(png_bytes)).convert("L")


def extract_warthog_throttle_cutouts(
    pdf_path: Path = TARGET_THROTTLE_PDF,
) -> Tuple[Optional[Image.Image], Optional[Image.Image]]:
    """
    Extrai as duas imagens recortadas com transparência (RGBA) de warthog_throttle.pdf:
      - Im1 (509x455): Vista completa da Base + Manetes Duplas (Stream 13 + SMask Stream 12)
      - Im0 (254x268): Vista aproximada dos Punhos da Manete (Stream 11 + SMask Stream 9)
    """
    if not pdf_path.exists():
        return None, None

    data = pdf_path.read_bytes()
    streams: List[Tuple[str, bytes]] = []
    for obj_chunk in data.split(b"endobj"):
        s_idx = obj_chunk.find(b"stream")
        if s_idx == -1:
            continue
        e_idx = obj_chunk.find(b"endstream", s_idx)
        if e_idx == -1:
            continue
        header = obj_chunk[:s_idx].decode("latin1", errors="ignore")
        raw = obj_chunk[s_idx + 6 : e_idx].strip(b"\r\n")
        streams.append((header, raw))

    # Procurar por dimensões nas streams
    im0_rgb: Optional[Image.Image] = None
    im0_mask: Optional[Image.Image] = None
    im1_rgb: Optional[Image.Image] = None
    im1_mask: Optional[Image.Image] = None

    for header, raw in streams:
        if "/Subtype/Image" not in header and "/Subtype /Image" not in header:
            continue
        w_m = re.search(r"/Width\s+(\d+)", header)
        h_m = re.search(r"/Height\s+(\d+)", header)
        if not (w_m and h_m):
            continue
        w, h = int(w_m.group(1)), int(h_m.group(1))
        if "/DCTDecode" in header:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            if (w, h) == (254, 268):
                im0_rgb = img
            elif (w, h) == (509, 455):
                im1_rgb = img
        elif "/FlateDecode" in header and "/DeviceGray" in header:
            try:
                mask = _wrap_pdf_predictor15_as_png(w, h, raw)
                if (w, h) == (254, 268):
                    im0_mask = mask
                elif (w, h) == (509, 455):
                    im1_mask = mask
            except Exception:
                pass

    im1_rgba = None
    if im1_rgb is not None:
        im1_rgba = im1_rgb.convert("RGBA")
        if im1_mask is not None:
            im1_rgba.putalpha(im1_mask)

    im0_rgba = None
    if im0_rgb is not None:
        im0_rgba = im0_rgb.convert("RGBA")
        if im0_mask is not None:
            im0_rgba.putalpha(im0_mask)

    return im1_rgba, im0_rgba


def generate_dual_throttle_annotated_diagram(output_path: Path) -> Path:
    """
    Gera o poster/diagrama oficial Ultra-HD (3368 x 2381 px) da Manete Dupla Warthog
    com todos os 32 botões, eixos, Coolie Hat e 5 LEDs mapeados para o Star Citizen 4.10.
    """
    scale = 4.0
    pdf_w, pdf_h = 841.89, 595.276
    W = int(round(pdf_w * scale))  # 3368
    H = int(round(pdf_h * scale))  # 2381

    def px(x_pdf: float, y_pdf: float) -> Tuple[int, int]:
        """Converte coordenadas PDF (origem inferior-esquerda) para pixels (origem superior-esquerda)."""
        return int(round(x_pdf * scale)), int(round((pdf_h - y_pdf) * scale))

    # Criar fundo táctico Star Citizen (Aegis / Crusader HUD)
    canvas = Image.new("RGBA", (W, H), (6, 11, 22, 255))
    draw = ImageDraw.Draw(canvas)

    # Grelha subtil de engenharia
    grid_step = int(20 * scale)
    for gx in range(0, W, grid_step):
        draw.line([(gx, 0), (gx, H)], fill=(14, 28, 50, 255), width=1)
    for gy in range(0, H, grid_step):
        draw.line([(0, gy), (W, gy)], fill=(14, 28, 50, 255), width=1)

    # Moldura exterior HUD
    pad = 24
    draw.rectangle([pad, pad, W - pad, H - pad], outline=(0, 190, 255, 160), width=3)
    draw.rectangle([pad + 8, pad + 8, W - pad - 8, H - pad - 8], outline=(0, 120, 180, 90), width=1)

    # Cabeçalho Principal no topo
    header_h = 128
    draw.rectangle([pad, pad, W - pad, pad + header_h], fill=(8, 20, 40, 240), outline=(0, 210, 255, 200), width=2)
    font_title = _get_font(40, bold=True)
    font_sub = _get_font(22, bold=False)
    draw.text(
        (pad + 32, pad + 20),
        "THRUSTMASTER HOTAS WARTHOG — MANETE DUPLA (DUAL THROTTLE)",
        font=font_title,
        fill=(0, 240, 255, 255),
    )
    draw.text(
        (pad + 32, pad + 74),
        "MAPA COMPLETO STAR CITIZEN 4.10  •  32 BOTÕES (B1..B32) + COOLIE HAT + 5 EIXOS + 5 LEDs  •  DISPOSITIVO: js2",
        font=font_sub,
        fill=(180, 220, 255, 255),
    )

    # Legenda de Cores no canto superior direito
    legend_items = [
        ((0, 240, 255), "VOO / PROPULSÃO / MODOS"),
        ((255, 165, 0), "ENERGIA / ARMAS / MOTORES"),
        ((0, 255, 136), "MINERAÇÃO / PORTAS / LEDs"),
    ]
    lx = W - 1060
    for color, label in legend_items:
        draw.rounded_rectangle([lx, pad + 42, lx + 28, pad + 70], radius=6, fill=color)
        draw.text((lx + 38, pad + 40), label, font=_get_font(19, bold=True), fill=(230, 245, 255))
        lx += 345

    # Extrair e colar imagens reais recortadas da Manete Dupla
    im1_rgba, im0_rgba = extract_warthog_throttle_cutouts()

    # Posição PDF de Im1: x=63.194, y=194.687, w=365.819, h=327.359
    if im1_rgba is not None:
        im1_w = int(round(365.8187 * scale))
        im1_h = int(round(327.3585 * scale))
        im1_x, im1_y = px(63.1943, 194.6869 + 327.3585)
        im1_resized = im1_rgba.resize((im1_w, im1_h), Image.Resampling.LANCZOS)
        # Halo ciano subtil atrás do hardware
        glow = im1_resized.split()[3].filter(ImageFilter.GaussianBlur(radius=14))
        glow_layer = Image.new("RGBA", (im1_w, im1_h), (0, 200, 255, 0))
        glow_layer.putalpha(glow.point(lambda a: min(110, int(a * 0.45))))
        canvas.alpha_composite(glow_layer, (im1_x, im1_y))
        canvas.alpha_composite(im1_resized, (im1_x, im1_y))

    # Posição PDF de Im0: x=578.042, y=151.567, w=182.544, h=192.800
    if im0_rgba is not None:
        im0_w = int(round(182.5444 * scale))
        im0_h = int(round(192.7997 * scale))
        im0_x, im0_y = px(578.0422, 151.5675 + 192.7997)
        im0_resized = im0_rgba.resize((im0_w, im0_h), Image.Resampling.LANCZOS)
        glow0 = im0_resized.split()[3].filter(ImageFilter.GaussianBlur(radius=14))
        glow0_layer = Image.new("RGBA", (im0_w, im0_h), (0, 200, 255, 0))
        glow0_layer.putalpha(glow0.point(lambda a: min(110, int(a * 0.45))))
        canvas.alpha_composite(glow0_layer, (im0_x, im0_y))
        canvas.alpha_composite(im0_resized, (im0_x, im0_y))

    draw = ImageDraw.Draw(canvas)

    # Cores temáticas por categoria
    C_FLIGHT = (0, 240, 255)   # Ciano
    C_POWER = (255, 165, 0)    # Laranja
    C_UTIL = (0, 255, 136)     # Verde Esmeralda

    # Lista completa de Callouts com coordenadas PDF exatas (adaptadas de warthog_throttle.pdf)
    # Cada item: (box_rect_pdf (x1, y1_bottom, x2, y2_top), polyline_pts_pdf, dot_pdf, color, title, badge, lines)
    callouts = [
        # --- PAINEL ESQUERDO DA BASE ---
        (
            (12, 400, 108, 466),
            [(108, 401.14), (162.75, 386.81)],
            (162.75, 386.81),
            C_FLIGHT,
            "FLAPS (3 Posições)",
            "B22 / B23",
            [
                ("FLAPU (B22 Cima):", "VTOL Vertical (K)"),
                ("FLAPM (Centro):", "Voo Normal (Pulso)"),
                ("FLAPD (B23 Baixo):", "Trem Aterragem (N)"),
            ],
        ),
        (
            (12, 296, 108, 360),
            [(108, 300.53), (124.99, 344.40)],
            (124.99, 344.40),
            C_FLIGHT,
            "EAC ARM / OFF",
            "B24",
            [
                ("EACON (B24 Cima):", "Master Mode NAV"),
                ("EACOFF (Baixo):", "Master Mode SCM"),
            ],
        ),
        (
            (12, 186, 122, 254),
            [(122, 251.60), (149.25, 321.31)],
            (149.25, 321.31),
            C_UTIL,
            "RDR ALTM (Faróis)",
            "B25",
            [
                ("RDRNRM (B25 Cima):", "Luzes da Nave ON (L)"),
                ("RDRDIS (Baixo):", "Luzes da Nave OFF"),
            ],
        ),
        (
            (12, 74, 132, 144),
            [(132, 139.99), (169.75, 302.81)],
            (169.75, 302.81),
            C_FLIGHT,
            "AUTOPILOT ENGAGE",
            "B26",
            [
                ("APENG (B26 Botão):", "Quantum Drive / Jump"),
                ("Aciona Spooling", "e Salto Quântico"),
            ],
        ),
        (
            (142, 74, 272, 144),
            [(190.75, 144.0), (190.75, 294.81)],
            (190.75, 294.81),
            C_UTIL,
            "AUTOPILOT SELECT (3 Pos)",
            "B27 / B28",
            [
                ("APPAT (B27 Cima):", "Abrir/Fechar Portas Ext."),
                ("APAH (Centro):", "Posição Neutra"),
                ("APALT (B28 Baixo):", "Trancar/Destrancar Portas"),
            ],
        ),
        (
            (184, 154, 302, 214),
            [(214.07, 214.0), (236.75, 321.31)],
            (236.75, 321.31),
            C_FLIGHT,
            "LANDING GEAR HORN",
            "B21",
            [
                ("LDGH (B21 Botão):", "Trem de Aterragem (N)"),
                ("Acesso Rápido", "Subir / Descer Trem"),
            ],
        ),
        (
            (256, 226, 384, 266),
            [(264.73, 257.89), (288.33, 316.81)],
            (288.33, 316.81),
            C_UTIL,
            "FRICTION CONTROL",
            "SLIDER 1",
            [
                ("Roda Analógica:", "Potência Laser Mineração"),
                ("Eixo js2_slider1:", "Controlo Fino de Feixe"),
            ],
        ),
        # --- PAINEL DIREITO DA BASE (MOTORES E ENERGIA) ---
        (
            (392, 360, 526, 422),
            [(392, 411.82), (345.33, 394.61)],
            (345.33, 394.61),
            C_POWER,
            "ENGINE FUEL FLOW LEFT",
            "B16",
            [
                ("EFLNORM (B16 Cima):", "Energia Geral ON (LAlt+L)"),
                ("EFLOVER (Baixo):", "Desligar Energia (Pulso)"),
            ],
        ),
        (
            (392, 292, 526, 352),
            [(392, 341.45), (371.75, 376.40)],
            (371.75, 376.40),
            C_POWER,
            "ENGINE FUEL FLOW RIGHT",
            "B17",
            [
                ("EFRNORM (B17 Cima):", "Armas ON / OFF (P)"),
                ("EFROVER (Baixo):", "Escudos ON / OFF (O)"),
            ],
        ),
        (
            (392, 206, 536, 282),
            [(392, 271.09), (355.75, 271.09), (355.75, 373.31), (295.75, 373.31)],
            (295.75, 373.31),
            C_POWER,
            "ENGINE OPERATE L / R",
            "B18/19/31/32",
            [
                ("IGN (B18/B19 Cima):", "Flight Ready (RAlt+R)"),
                ("NORM (Centro):", "Posição Normal"),
                ("MOTOR (B31/B32 Baixo):", "Motores ON/OFF (I)"),
            ],
        ),
        (
            (310, 144, 456, 198),
            [(355.75, 198.0), (330.83, 357.81)],
            (330.83, 357.81),
            C_POWER,
            "APU START + IDLE CUTOFF",
            "B20 / B29 / B30",
            [
                ("APU (B20 Cima):", "Ligar/Desligar Motores (I)"),
                ("CUTOFF (B29/B30):", "Corte Turbinas no Batente"),
            ],
        ),
        # --- 5 LEDs NO TOPO DA BASE ---
        (
            (172, 486, 224, 534),
            [(198.0, 486.0), (318.75, 394.28)],
            (318.75, 394.28),
            C_UTIL,
            "LED 5",
            "AUX",
            [("Indicador:", "Flaps / Aux")],
        ),
        (
            (226, 486, 278, 534),
            [(248.0, 486.0), (325.56, 397.53)],
            (325.56, 397.53),
            C_UTIL,
            "LED 4",
            "TREM",
            [("Indicador:", "Trem Descido")],
        ),
        (
            (280, 486, 332, 534),
            [(299.0, 486.0), (332.38, 400.53)],
            (332.38, 400.53),
            C_UTIL,
            "LED 3",
            "VTOL",
            [("Indicador:", "Modo VTOL")],
        ),
        (
            (334, 486, 386, 534),
            [(349.33, 486.0), (338.56, 406.09)],
            (338.56, 406.09),
            C_UTIL,
            "LED 2",
            "MODO",
            [("Indicador:", "NAV / SCM")],
        ),
        (
            (388, 486, 440, 534),
            [(398.67, 486.0), (346.00, 407.03)],
            (346.00, 407.03),
            C_UTIL,
            "LED 1",
            "SISTEMA",
            [("Indicador:", "Flight Ready")],
        ),
        # --- PUNHOS DAS MANETES (VISTA LATERAL / FRONTAL) ---
        (
            (410, 428, 526, 496),
            [(526, 435.0), (547.09, 435.0), (547.09, 297.61), (593.75, 268.81)],
            (593.75, 268.81),
            C_FLIGHT,
            "SPEEDBRAKE (Travão/Boost)",
            "B7 / B8",
            [
                ("SPDF (B7 Frente):", "Spacebrake / Travão (X)"),
                ("SPDB (B8 Trás):", "Boost / Afterburner"),
            ],
        ),
        (
            (462, 68, 576, 140),
            [(564.75, 140.0), (589.25, 246.31)],
            (589.25, 246.31),
            C_UTIL,
            "BOAT SWITCH (3 Posições)",
            "B9 / B10",
            [
                ("BSF (B9 Frente):", "Modo Mineração / Salvage"),
                ("BSM (Centro):", "Modo Combate Normal"),
                ("BSB (B10 Trás):", "Modo Scanner (V)"),
            ],
        ),
        (
            (582, 68, 688, 140),
            [(601.67, 140.0), (595.25, 214.31)],
            (595.25, 214.31),
            C_UTIL,
            "CHINA HAT (Radar / Ping)",
            "B11 / B12",
            [
                ("CHF (B11 Frente):", "Ping de Radar Ativo"),
                ("CHB (B12 Trás):", "Jettison Cargo / Recolha"),
            ],
        ),
        (
            (608, 148, 704, 184),
            [(694.25, 179.54), (687.91, 188.31)],
            (687.91, 188.31),
            C_FLIGHT,
            "MANETE DIREITA",
            "EIXO Z",
            [("js2_z:", "Acelerador Principal")],
        ),
        (
            (694, 98, 828, 140),
            [(698.07, 140.0), (718.91, 187.65)],
            (718.91, 187.65),
            C_FLIGHT,
            "MANETE ESQUERDA",
            "EIXO Rz",
            [("js2_rotz:", "Speed Limiter (Relativo)")],
        ),
        (
            (726, 160, 832, 232),
            [(743.68, 232.0), (751.75, 271.31)],
            (751.75, 271.31),
            C_FLIGHT,
            "PINKY SWITCH (Mindinho)",
            "B13 / B14",
            [
                ("PSF (B13 Frente):", "Coupled / Decoupled"),
                ("PSM (Centro):", "Voo Normal"),
                ("PSB (B14 Trás):", "ESP Toggle"),
            ],
        ),
        (
            (708, 326, 832, 378),
            [(715.68, 326.0), (744.25, 299.31)],
            (744.25, 299.31),
            C_FLIGHT,
            "LEFT THROTTLE BUTTON",
            "B15",
            [
                ("LTB (B15 Botão):", "Autoland / Aterragem Auto"),
                ("Manter Premido:", "Pouso Automático (N)"),
            ],
        ),
        (
            (688, 386, 832, 440),
            [(693.72, 386.0), (693.25, 303.81)],
            (693.25, 303.81),
            C_FLIGHT,
            "SLEW CONTROL (Mini-Stick)",
            "EIXOS X/Y + B1",
            [
                ("Mini-Stick X / Y:", "Strafe Lateral / Vertical"),
                ("SC Push (B1):", "Match Target Velocity"),
            ],
        ),
        (
            (654, 446, 832, 534),
            [(656.72, 446.0), (668.91, 311.31)],
            (668.91, 311.31),
            C_FLIGHT,
            "COOLIE SWITCH (Hat Frontal)",
            "POV 1 (4 Vias)",
            [
                ("CSU (Cima):", "Strafe Vertical Cima"),
                ("CSD (Baixo):", "Strafe Vertical Baixo"),
                ("CSL / CSR (Esq/Dir):", "Strafe Esquerda / Direita"),
            ],
        ),
        (
            (528, 456, 648, 552),
            [(643.08, 456.0), (583.50, 307.78)],
            (583.50, 307.78),
            C_POWER,
            "MIC SWITCH (Energia 5 Vias)",
            "B2 .. B6",
            [
                ("MSU (B3 Cima):", "Energia -> ESCUDOS"),
                ("MSR (B4 Direita):", "Energia -> MOTORES"),
                ("MSL (B6 Esquerda):", "Energia -> ARMAS"),
                ("MSP/MSD (B2/B5):", "Reset Energia (Balance)"),
            ],
        ),
    ]

    # Desenhar primeiro todas as linhas de chamada e pontos-alvo no hardware
    for _, poly_pdf, dot_pdf, color, _, _, _ in callouts:
        if len(poly_pdf) >= 2:
            pts = [px(pt[0], pt[1]) for pt in poly_pdf]
            # Sombra da linha para contraste sobre a foto
            draw.line(pts, fill=(0, 0, 0, 220), width=7, joint="curve")
            draw.line(pts, fill=(*color, 240), width=3, joint="curve")
        dx, dy = px(dot_pdf[0], dot_pdf[1])
        r_outer = 12
        r_inner = 6
        draw.ellipse([dx - r_outer, dy - r_outer, dx + r_outer, dy + r_outer], fill=(0, 0, 0, 200), outline=(*color, 255), width=3)
        draw.ellipse([dx - r_inner, dy - r_inner, dx + r_inner, dy + r_inner], fill=(255, 255, 255, 255))

    # Fontes para os cartões de chamada
    f_card_title = _get_font(19, bold=True)
    f_badge = _get_font(16, bold=True)
    f_key = _get_font(16, bold=True)
    f_val = _get_font(16, bold=False)

    # Desenhar os cartões de chamada (Callout Boxes)
    for (x1_p, y1_p, x2_p, y2_p), _, _, color, title, badge, lines in callouts:
        x1, y2 = px(x1_p, y1_p)
        x2, y1 = px(x2_p, y2_p)
        # Fundo vidro escuro (Glassmorphism)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=(8, 16, 32, 240), outline=(*color, 230), width=3)
        # Barra de topo do cartão (azul marinho escuro para contraste perfeito com texto colorido)
        header_bar_h = 34
        draw.rounded_rectangle([x1 + 2, y1 + 2, x2 - 2, y1 + header_bar_h], radius=8, fill=(16, 34, 64, 255))
        draw.line([(x1, y1 + header_bar_h), (x2, y1 + header_bar_h)], fill=(*color, 190), width=2)

        # Título e Badge do Botão
        draw.text((x1 + 10, y1 + 5), title, font=f_card_title, fill=(*color, 255))
        if badge:
            tw = int(draw.textlength(badge, font=f_badge))
            bx1 = x2 - tw - 18
            draw.rounded_rectangle([bx1, y1 + 5, x2 - 6, y1 + header_bar_h - 4], radius=5, fill=(*color, 255))
            draw.text((bx1 + 6, y1 + 5), badge, font=f_badge, fill=(5, 10, 20, 255))

        # Linhas de função Star Citizen
        cy = y1 + header_bar_h + 7
        line_step = max(21, min(26, (y2 - cy - 6) // max(1, len(lines))))
        for k_txt, v_txt in lines:
            draw.text((x1 + 10, cy), k_txt, font=f_key, fill=(175, 210, 240, 255))
            kw = int(draw.textlength(k_txt, font=f_key))
            draw.text((x1 + 16 + kw, cy), v_txt, font=f_val, fill=(255, 255, 255, 255))
            cy += line_step

    # Rodapé informativo
    footer_y = H - 64
    draw.text(
        (pad + 24, footer_y),
        "SC WARTHOG COMMANDER  •  PRONTO PARA IMPRESSÃO / CONSULTA RÁPIDA  •  RETROILUMINAÇÃO E 5 LEDs ATIVOS VIA HID 36-BYTE REPORT",
        font=_get_font(18, bold=True),
        fill=(0, 200, 255, 200),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, "PNG", optimize=True)
    return output_path


def _heightmap_to_watertight_stl(
    solid_mask: np.ndarray,
    z_top: np.ndarray,
    pixel_size_mm: float,
    stl_path: Path,
    header_text: str = "SC Warthog 3D Printable Plate",
) -> int:
    """
    Converte uma grelha 2D (solid_mask[ny, nx], z_top[ny, nx]) num ficheiro .STL binário
    100% estanque (watertight manifold) usando Greedy Meshing 2D para as faces de topo/base
    e fusão de segmentos para as paredes verticais.
    Retorna o número total de triângulos gerados.
    """
    ny, nx = solid_mask.shape
    dx = dy = float(pixel_size_mm)

    # Quantizar z_top em centésimos de milímetro para comparação exata no Greedy Meshing
    z_quant = np.where(solid_mask, np.rint(z_top * 100.0).astype(np.int32), 0)

    triangles: List[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]] = []

    # 1. Faces horizontais (Topo z=z_top e Base z=0.0) via Greedy Meshing 2D por nível Z
    visited = ~solid_mask.copy()
    for iy in range(ny):
        ix = 0
        while ix < nx:
            if visited[iy, ix]:
                ix += 1
                continue
            zq = z_quant[iy, ix]
            z_val = float(z_top[iy, ix])
            # Expandir em X
            w = 1
            while ix + w < nx and (not visited[iy, ix + w]) and z_quant[iy, ix + w] == zq:
                w += 1
            # Expandir em Y
            h = 1
            while iy + h < ny:
                row_ok = True
                for kx in range(ix, ix + w):
                    if visited[iy + h, kx] or z_quant[iy + h, kx] != zq:
                        row_ok = False
                        break
                if not row_ok:
                    break
                h += 1
            visited[iy : iy + h, ix : ix + w] = True

            x0 = ix * dx
            x1 = (ix + w) * dx
            # Inverter Y para que o topo da imagem corresponda a Y positivo no modelo 3D
            y0 = (ny - (iy + h)) * dy
            y1 = (ny - iy) * dy

            # Face de Topo (normal +Z)
            triangles.append(((0.0, 0.0, 1.0), (x0, y0, z_val), (x1, y0, z_val), (x1, y1, z_val)))
            triangles.append(((0.0, 0.0, 1.0), (x0, y0, z_val), (x1, y1, z_val), (x0, y1, z_val)))

            # Face de Base em z=0.0 (normal -Z)
            triangles.append(((0.0, 0.0, -1.0), (x0, y0, 0.0), (x1, y1, 0.0), (x1, y0, 0.0)))
            triangles.append(((0.0, 0.0, -1.0), (x0, y0, 0.0), (x0, y1, 0.0), (x1, y1, 0.0)))

            ix += w

    # 2. Paredes Verticais paralelas a Y (entre ix-1 e ix)
    for ix in range(nx + 1):
        x_coord = ix * dx
        iy = 0
        while iy < ny:
            left_zq = z_quant[iy, ix - 1] if ix > 0 else 0
            right_zq = z_quant[iy, ix] if ix < nx else 0
            if left_zq == right_zq:
                iy += 1
                continue
            h = 1
            while iy + h < ny:
                lz = z_quant[iy + h, ix - 1] if ix > 0 else 0
                rz = z_quant[iy + h, ix] if ix < nx else 0
                if lz != left_zq or rz != right_zq:
                    break
                h += 1
            y0 = (ny - (iy + h)) * dy
            y1 = (ny - iy) * dy
            z_low = min(left_zq, right_zq) / 100.0
            z_high = max(left_zq, right_zq) / 100.0
            if left_zq > right_zq:
                # Normal aponta para +X
                n = (1.0, 0.0, 0.0)
                triangles.append((n, (x_coord, y0, z_low), (x_coord, y1, z_low), (x_coord, y1, z_high)))
                triangles.append((n, (x_coord, y0, z_low), (x_coord, y1, z_high), (x_coord, y0, z_high)))
            else:
                # Normal aponta para -X
                n = (-1.0, 0.0, 0.0)
                triangles.append((n, (x_coord, y0, z_low), (x_coord, y1, z_high), (x_coord, y1, z_low)))
                triangles.append((n, (x_coord, y0, z_low), (x_coord, y0, z_high), (x_coord, y1, z_high)))
            iy += h

    # 3. Paredes Verticais paralelas a X (entre iy-1 e iy)
    for iy in range(ny + 1):
        y_coord = (ny - iy) * dy
        ix = 0
        while ix < nx:
            top_zq = z_quant[iy - 1, ix] if iy > 0 else 0
            bot_zq = z_quant[iy, ix] if iy < ny else 0
            if top_zq == bot_zq:
                ix += 1
                continue
            w = 1
            while ix + w < nx:
                tz = z_quant[iy - 1, ix + w] if iy > 0 else 0
                bz = z_quant[iy, ix + w] if iy < ny else 0
                if tz != top_zq or bz != bot_zq:
                    break
                w += 1
            x0 = ix * dx
            x1 = (ix + w) * dx
            z_low = min(top_zq, bot_zq) / 100.0
            z_high = max(top_zq, bot_zq) / 100.0
            if bot_zq > top_zq:
                # Normal aponta para +Y
                n = (0.0, 1.0, 0.0)
                triangles.append((n, (x0, y_coord, z_low), (x1, y_coord, z_high), (x1, y_coord, z_low)))
                triangles.append((n, (x0, y_coord, z_low), (x0, y_coord, z_high), (x1, y_coord, z_high)))
            else:
                # Normal aponta para -Y
                n = (0.0, -1.0, 0.0)
                triangles.append((n, (x0, y_coord, z_low), (x1, y_coord, z_low), (x1, y_coord, z_high)))
                triangles.append((n, (x0, y_coord, z_low), (x1, y_coord, z_high), (x0, y_coord, z_high)))
            ix += w

    # Escrever ficheiro binário STL
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    hdr = header_text.encode("ascii", errors="ignore")[:80].ljust(80, b" ")
    with open(stl_path, "wb") as f:
        f.write(hdr)
        f.write(struct.pack("<I", len(triangles)))
        buf = bytearray(50 * len(triangles))
        offset = 0
        for n, v1, v2, v3 in triangles:
            struct.pack_into(
                "<12fH",
                buf,
                offset,
                n[0], n[1], n[2],
                v1[0], v1[1], v1[2],
                v2[0], v2[1], v2[2],
                v3[0], v3[1], v3[2],
                0,
            )
            offset += 50
        f.write(buf)

    return len(triangles)


def generate_3d_printable_throttle_plates(
    stl_faceplate_path: Path,
    stl_board_path: Path,
    svg_path: Path,
    preview_png_path: Path,
) -> Dict[str, int]:
    """
    Gera:
      1. warthog_throttle_placa_base_3d.stl: Placa física 1:1 (146 x 124 x 2.8 mm)
         com furos reais para os interruptores da base da Manete Dupla, 5 LEDs,
         rasgo para as manetes e letras 3D em alto-relevo (+0.8 mm).
      2. warthog_manete_dupla_quadro_3d.stl: Quadro/Placa 3D completa (200 x 142 x 2.6 mm)
         com a Base + Punhos + todos os 32 botões em alto-relevo para colocar na secretária.
      3. warthog_throttle_placa_1para1.svg: Molde vetorial 1:1 em milímetros.
      4. warthog_throttle_placa_3d_preview.png: Renderização 3D sombreada de alta resolução.
    """
    # =========================================================================
    # MODELO 1: PLACA ENCAIXÁVEL NA BASE DA MANETE DUPLA (146 x 124 x 2.8 mm)
    # =========================================================================
    plate_w_mm = 146.0
    plate_h_mm = 124.0
    px_mm = 0.20  # 0.20 mm por pixel (730 x 620 px) - alta precisão para impressoras FDM 0.4mm
    nx = int(round(plate_w_mm / px_mm))
    ny = int(round(plate_h_mm / px_mm))

    def mm(val: float) -> int:
        return int(round(val / px_mm))

    # Máscara da base sólida (True = plástico, False = furo passante)
    solid_img = Image.new("L", (nx, ny), 0)
    s_draw = ImageDraw.Draw(solid_img)
    # Placa com cantos arredondados (raio 6 mm)
    s_draw.rounded_rectangle([0, 0, nx - 1, ny - 1], radius=mm(6.0), fill=255)

    # Rasgo central esquerdo para o curso das manetes (Throttle Left/Right + Roda de Fricção)
    # Permite encaixar a placa na consola sem desmontar os punhos!
    slot_x1, slot_y1, slot_x2, slot_y2 = 42.0, 0.0, 82.0, 64.0
    s_draw.rounded_rectangle([mm(slot_x1), mm(slot_y1), mm(slot_x2), mm(slot_y2)], radius=mm(4.0), fill=0)

    # Definição dos Furos dos Interruptores (coordenadas em mm na placa 146 x 124 mm)
    # (cx_mm, cy_mm, diametro_furo_mm, titulo_topo, label_cima, label_baixo, codigo_botao)
    switches_spec = [
        # Coluna Esquerda (FLAPS, EAC, RDR ALTM, APENG)
        (21.0, 22.0, 12.2, "FLAPS", "B22 VTOL", "B23 TREM", "3-POS"),
        (21.0, 50.0, 12.2, "EAC MODE", "B24 MODO NAV", "MODO SCM", "2-POS"),
        (21.0, 78.0, 12.2, "RDR ALTM", "B25 LUZES ON", "LUZES OFF", "2-POS"),
        (21.0, 105.0, 10.6, "AUTOPILOT", "B26 QUANTUM", "JUMP / TRAVEL", "PUSH"),
        # Zona Central-Inferior (LDGH, APPAT/AH/ALT)
        (62.0, 79.0, 10.6, "LDG HORN", "B21 TREM", "ATERRAGEM (N)", "PUSH"),
        (62.0, 105.0, 12.2, "AP SELECT", "B27 ABRIR PORTA", "B28 TRANCAR", "3-POS"),
        # Painel Direito Superior (FUEL FLOW L / R)
        (103.0, 34.0, 12.2, "FUEL LEFT", "B16 ENERGIA ON", "ENERGIA OFF", "2-POS"),
        (130.0, 34.0, 12.2, "FUEL RIGHT", "B17 ARMAS ON", "ESCUDOS ON", "2-POS"),
        # Painel Direito Médio (ENGINE OPERATE L / R)
        (103.0, 66.0, 12.2, "ENG LEFT", "B18 FLIGHT RDY", "B31 MOTOR ON", "3-POS"),
        (130.0, 66.0, 12.2, "ENG RIGHT", "B19 FLIGHT RDY", "B32 MOTOR ON", "3-POS"),
        # Painel Direito Inferior (APU START)
        (116.5, 98.0, 12.2, "APU START", "B20 MOTORES ON", "B29/30 CUTOFF", "2-POS"),
    ]

    # 5 Furos dos LEDs no topo direito (acima de Fuel Flow L/R)
    leds_spec = [
        (93.0, 12.0, 3.6, "L5", "AUX"),
        (104.5, 12.0, 3.6, "L4", "TREM"),
        (116.0, 12.0, 3.6, "L3", "VTOL"),
        (127.5, 12.0, 3.6, "L2", "NAV"),
        (139.0, 12.0, 3.6, "L1", "RDY"),
    ]

    # Abrir furos circulares na máscara sólida
    for cx, cy, diam, _, _, _, _ in switches_spec:
        r = diam / 2.0
        s_draw.ellipse([mm(cx - r), mm(cy - r), mm(cx + r), mm(cy + r)], fill=0)

    for cx, cy, diam, _, _ in leds_spec:
        r = diam / 2.0
        s_draw.ellipse([mm(cx - r), mm(cy - r), mm(cx + r), mm(cy + r)], fill=0)

    # Criar máscara de Alto-Relevo (+0.8 mm acima da base de 2.0 mm -> total 2.8 mm)
    relief_img = Image.new("L", (nx, ny), 0)
    r_draw = ImageDraw.Draw(relief_img)

    # Moldura exterior em alto-relevo (espessura 1.8 mm)
    r_draw.rounded_rectangle([mm(1.2), mm(1.2), nx - mm(1.2) - 1, ny - mm(1.2) - 1], radius=mm(5.0), outline=255, width=mm(1.6))

    # Moldura em redor do rasgo das manetes
    r_draw.rounded_rectangle(
        [mm(slot_x1 - 1.4), mm(slot_y1), mm(slot_x2 + 1.4), mm(slot_y2 + 1.4)],
        radius=mm(4.8),
        outline=255,
        width=mm(1.4),
    )

    # Fontes para texto 3D (traço forte para fatiamento perfeito em bico 0.4mm)
    f_3d_sm = _get_font(mm(3.1), bold=True)
    f_3d_md = _get_font(mm(3.4), bold=True)
    f_3d_lg = _get_font(mm(4.0), bold=True)

    def _draw_centered_3d_text(cx_mm: float, cy_mm: float, text: str, font: ImageFont.FreeTypeFont) -> None:
        tw = r_draw.textlength(text, font=font)
        tx = int(round(mm(cx_mm) - tw / 2.0))
        ty = int(round(mm(cy_mm) - font.size / 2.0))
        r_draw.text((tx, ty), text, font=font, fill=255)

    # Título na base direita inferior
    _draw_centered_3d_text(116.5, 116.5, "STAR CITIZEN WARTHOG", f_3d_md)

    # Anéis de reforço e etiquetas 3D em cada interruptor
    for cx, cy, diam, _, lbl_up, lbl_dn, _ in switches_spec:
        r_ring = diam / 2.0 + 1.4
        r_draw.ellipse([mm(cx - r_ring), mm(cy - r_ring), mm(cx + r_ring), mm(cy + r_ring)], outline=255, width=mm(1.2))
        _draw_centered_3d_text(cx, cy - diam / 2.0 - 4.8, lbl_up, f_3d_sm)
        _draw_centered_3d_text(cx, cy + diam / 2.0 + 4.2, lbl_dn, f_3d_sm)

    # Anéis e etiquetas dos 5 LEDs
    for cx, cy, diam, l_num, l_txt in leds_spec:
        r_ring = diam / 2.0 + 1.0
        r_draw.ellipse([mm(cx - r_ring), mm(cy - r_ring), mm(cx + r_ring), mm(cy + r_ring)], outline=255, width=mm(1.0))
        _draw_centered_3d_text(cx, cy - 5.2, l_num, f_3d_sm)
        _draw_centered_3d_text(cx, cy + 5.0, l_txt, f_3d_sm)

    # Converter máscaras para matrizes NumPy e gerar STL #1
    solid_mask = np.array(solid_img) > 127
    relief_mask = (np.array(relief_img) > 127) & solid_mask
    z_top = np.where(relief_mask, 2.80, np.where(solid_mask, 2.00, 0.0)).astype(np.float32)

    tris_faceplate = _heightmap_to_watertight_stl(
        solid_mask=solid_mask,
        z_top=z_top,
        pixel_size_mm=px_mm,
        stl_path=stl_faceplate_path,
        header_text="Warthog Dual Throttle Base Faceplate SC 4.10 (146x124x2.8mm)",
    )

    # =========================================================================
    # MODELO 2: QUADRO 3D COMPLETO DA MANETE DUPLA + PUNHOS (200 x 142 x 2.6 mm)
    # =========================================================================
    board_w_mm = 200.0
    board_h_mm = 142.0
    b_px_mm = 0.25  # 800 x 568 px
    bnx = int(round(board_w_mm / b_px_mm))
    bny = int(round(board_h_mm / b_px_mm))

    def bmm(val: float) -> int:
        return int(round(val / b_px_mm))

    b_solid_img = Image.new("L", (bnx, bny), 0)
    bs_draw = ImageDraw.Draw(b_solid_img)
    bs_draw.rounded_rectangle([0, 0, bnx - 1, bny - 1], radius=bmm(5.0), fill=255)
    # Dois furos de 4.0mm nos cantos superiores para pendurar ou suporte de secretária
    bs_draw.ellipse([bmm(6.0), bmm(6.0), bmm(10.0), bmm(10.0)], fill=0)
    bs_draw.ellipse([bnx - bmm(10.0), bmm(6.0), bnx - bmm(6.0), bmm(10.0)], fill=0)

    b_relief_img = Image.new("L", (bnx, bny), 0)
    br_draw = ImageDraw.Draw(b_relief_img)
    br_draw.rounded_rectangle([bmm(1.5), bmm(1.5), bnx - bmm(1.5) - 1, bny - bmm(1.5) - 1], radius=bmm(4.5), outline=255, width=bmm(1.5))
    # Divisória central entre PUNHOS (Esquerda) e BASE (Direita)
    br_draw.line([(bmm(100.0), bmm(16.0)), (bmm(100.0), bny - bmm(4.0))], fill=255, width=bmm(1.2))
    br_draw.line([(bmm(2.0), bmm(16.0)), (bnx - bmm(2.0), bmm(16.0))], fill=255, width=bmm(1.2))

    bf_title = _get_font(bmm(4.5), bold=True)
    bf_sec = _get_font(bmm(3.5), bold=True)
    bf_row = _get_font(bmm(2.9), bold=True)

    br_draw.text((bmm(14.0), bmm(4.4)), "TODOS OS 19 INTERRUPTORES FISICOS DA MANETE DUPLA (32 BOTOES)", font=bf_title, fill=255)

    def _draw_switch_icon(kind: str, cx_m: float, cy_m: float) -> None:
        cx_p, cy_p = bmm(cx_m), bmm(cy_m)
        r = bmm(2.4)
        if kind == "hat":
            # Cruz direcional (Coolie / MIC / Slew)
            br_draw.polygon(
                [
                    (cx_p, cy_p - r),
                    (cx_p + r, cy_p),
                    (cx_p, cy_p + r),
                    (cx_p - r, cy_p),
                ],
                outline=255,
                width=bmm(0.7),
            )
            br_draw.ellipse([cx_p - bmm(0.8), cy_p - bmm(0.8), cx_p + bmm(0.8), cy_p + bmm(0.8)], fill=255)
        elif kind == "rocker":
            # Interruptor retangular 3 posições (Speedbrake / Boat / China Hat)
            br_draw.rounded_rectangle([cx_p - r, cy_p - bmm(1.8), cx_p + r, cy_p + bmm(1.8)], radius=bmm(0.8), outline=255, width=bmm(0.7))
            br_draw.line([(cx_p, cy_p - bmm(1.8)), (cx_p, cy_p + bmm(1.8))], fill=255, width=bmm(0.6))
        elif kind == "push":
            # Botão de pressão redondo (LTB / LDGH / APENG)
            br_draw.ellipse([cx_p - r, cy_p - r, cx_p + r, cy_p + r], outline=255, width=bmm(0.7))
            br_draw.ellipse([cx_p - bmm(1.1), cy_p - bmm(1.1), cx_p + bmm(1.1), cy_p + bmm(1.1)], fill=255)
        elif kind == "axis":
            # Eixo / Slider linear
            br_draw.rounded_rectangle([cx_p - r, cy_p - bmm(1.2), cx_p + r, cy_p + bmm(1.2)], radius=bmm(0.6), outline=255, width=bmm(0.6))
            br_draw.rectangle([cx_p - bmm(0.7), cy_p - bmm(2.0), cx_p + bmm(0.7), cy_p + bmm(2.0)], fill=255)
        else:
            # Alavanca metálica Toggle (2 ou 3 posições)
            br_draw.ellipse([cx_p - r, cy_p - r, cx_p + r, cy_p + r], outline=255, width=bmm(0.7))
            br_draw.line([(cx_p, cy_p), (cx_p, cy_p - r - bmm(0.6))], fill=255, width=bmm(0.9))

    # Coluna Esquerda: 10 CONTROLOS FÍSICOS NOS PUNHOS (B1..B15 + POV1 + EIXOS)
    br_draw.text((bmm(5.0), bmm(18.5)), "PUNHOS ESQ/DIR (10 INTERRUPTORES/EIXOS)", font=bf_sec, fill=255)
    grip_rows = [
        ("axis", "1. MANETE DIR (EIXO Z): ACELERADOR"),
        ("axis", "2. MANETE ESQ (EIXO Rz): SPEED LIMIT"),
        ("hat", "3. SLEW MINI-STICK (X/Y): STRAFE 2D"),
        ("push", "4. SLEW PUSH (B1): MATCH VELOCITY"),
        ("hat", "5. COOLIE HAT (POV1): STRAFE 4 VIAS"),
        ("hat", "6. MIC SWITCH (B2..B6): ENERGIA 5 VIAS"),
        ("rocker", "7. SPEEDBRAKE (B7/B8): TRAVAO / BOOST"),
        ("rocker", "8. BOAT SWITCH (B9/B10): MINER / SCAN"),
        ("rocker", "9. CHINA HAT (B11/B12): PING / CARGO"),
        ("toggle", "10. PINKY (B13/B14): DECOUPLED / ESP"),
        ("push", "11. LEFT BTN (B15): AUTOLAND (N HOLD)"),
        ("toggle", "12. CUTOFF L/R (B29/B30): STOP MOTOR"),
    ]
    gy = 28.0
    for kind, row_txt in grip_rows:
        _draw_switch_icon(kind, 7.5, gy + 1.8)
        br_draw.text((bmm(11.8), bmm(gy)), row_txt, font=bf_row, fill=255)
        gy += 9.1

    # Coluna Direita: 11 INTERRUPTORES FÍSICOS DA BASE + RODA + 5 LEDs
    br_draw.text((bmm(103.5), bmm(18.5)), "CONSOLA DA BASE (11 SWITCHES + LEDS)", font=bf_sec, fill=255)
    base_rows = [
        ("axis", "13. RODA FRICCAO (SLIDER1): MINERACAO"),
        ("toggle", "14. EFL NORM/OVER (B16): ENERGIA ON/OFF"),
        ("toggle", "15. EFR NORM/OVER (B17): ARMAS/ESCUDOS"),
        ("toggle", "16. ENG OPER L (B18/B31): IGN / MOTOR L"),
        ("toggle", "17. ENG OPER R (B19/B32): IGN / MOTOR R"),
        ("toggle", "18. APU START/OFF (B20): MOTORES ON/OFF"),
        ("push", "19. L/G HORN BTN (B21): TREM ATERR. (N)"),
        ("toggle", "20. FLAPS UP/MVR/DN (B22/23): VTOL/TREM"),
        ("toggle", "21. EAC ARM/OFF (B24): MODO NAV / SCM"),
        ("toggle", "22. RDR ALTM NRM/DIS (B25): LUZES (L)"),
        ("push", "23. AP ENGAGE BTN (B26): QUANTUM JUMP"),
        ("toggle", "24. AP PATH/AH/ALT (B27/28): PORTAS"),
    ]
    by = 28.0
    for kind, row_txt in base_rows:
        _draw_switch_icon(kind, 106.0, by + 1.8)
        br_draw.text((bmm(110.3), bmm(by)), row_txt, font=bf_row, fill=255)
        by += 9.1

    b_solid = np.array(b_solid_img) > 127
    b_relief = (np.array(b_relief_img) > 127) & b_solid
    b_z_top = np.where(b_relief, 2.40, np.where(b_solid, 1.60, 0.0)).astype(np.float32)

    tris_board = _heightmap_to_watertight_stl(
        solid_mask=b_solid,
        z_top=b_z_top,
        pixel_size_mm=b_px_mm,
        stl_path=stl_board_path,
        header_text="Warthog Dual Throttle Complete 3D Reference Board (200x142x2.4mm)",
    )

    # =========================================================================
    # MODELO 3: FICHEIRO VETORIAL .SVG 1:1 (146mm x 124mm) PARA CORTE / IMPRESSÃO
    # =========================================================================
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{plate_w_mm}mm" height="{plate_h_mm}mm" viewBox="0 0 {plate_w_mm} {plate_h_mm}">',
        '  <rect x="0.5" y="0.5" width="145" height="123" rx="6" ry="6" fill="#0b1528" stroke="#00f0ff" stroke-width="1.2"/>',
        f'  <rect x="{slot_x1}" y="{slot_y1}" width="{slot_x2 - slot_x1}" height="{slot_y2 - slot_y1}" rx="4" ry="4" fill="#000000" stroke="#00f0ff" stroke-width="0.8"/>',
    ]
    for cx, cy, diam, _, lbl_up, lbl_dn, _ in switches_spec:
        r = diam / 2.0
        svg_lines.append(f'  <circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="#000000" stroke="#ff9d00" stroke-width="0.8"/>')
        svg_lines.append(f'  <text x="{cx}" y="{cy - r - 3.2:.2f}" fill="#00f0ff" font-family="Segoe UI, Arial" font-size="3.0" font-weight="bold" text-anchor="middle">{lbl_up}</text>')
        svg_lines.append(f'  <text x="{cx}" y="{cy + r + 4.8:.2f}" fill="#ffffff" font-family="Segoe UI, Arial" font-size="3.0" font-weight="bold" text-anchor="middle">{lbl_dn}</text>')
    for cx, cy, diam, l_num, l_txt in leds_spec:
        r = diam / 2.0
        svg_lines.append(f'  <circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="#000000" stroke="#00ff88" stroke-width="0.6"/>')
        svg_lines.append(f'  <text x="{cx}" y="{cy - 3.8:.2f}" fill="#00ff88" font-family="Segoe UI, Arial" font-size="2.8" font-weight="bold" text-anchor="middle">{l_num}</text>')
        svg_lines.append(f'  <text x="{cx}" y="{cy + 5.6:.2f}" fill="#ffffff" font-family="Segoe UI, Arial" font-size="2.6" font-weight="bold" text-anchor="middle">{l_txt}</text>')
    svg_lines.append('  <text x="116.5" y="117.5" fill="#00f0ff" font-family="Segoe UI, Arial" font-size="3.6" font-weight="bold" text-anchor="middle">STAR CITIZEN WARTHOG</text>')
    svg_lines.append("</svg>")
    svg_path.write_text("\n".join(svg_lines), encoding="utf-8")

    # =========================================================================
    # MODELO 4: PREVIEW 3D SOMBREADO (RENDERIZAÇÃO DAS DUAS PLACAS 3D)
    # =========================================================================
    prev_w, prev_h = 2200, 1180
    prev = Image.new("RGB", (prev_w, prev_h), (7, 12, 24))
    p_draw = ImageDraw.Draw(prev)

    # Cabeçalho do Preview 3D
    p_draw.rectangle([20, 20, prev_w - 20, 110], fill=(12, 24, 48), outline=(0, 210, 255), width=2)
    p_draw.text(
        (44, 34),
        "MODELOS 3D (.STL) PARA IMPRESSORA 3D — MANETE DUPLA WARTHOG (STAR CITIZEN)",
        font=_get_font(30, bold=True),
        fill=(0, 240, 255),
    )
    p_draw.text(
        (44, 72),
        "Prontos para Bambu Studio / PrusaSlicer / Cura  •  Dica: Adicione Pausa/Troca de Filamento na camada Z = 2.0 mm para letras em cor contrastante!",
        font=_get_font(19, bold=False),
        fill=(200, 230, 255),
    )

    def _render_shaded_plate(s_mask: np.ndarray, r_mask: np.ndarray, target_size: Tuple[int, int]) -> Image.Image:
        """Renderiza uma vista 3D chanfrada com iluminação direcional e sombra projetada."""
        h_m, w_m = s_mask.shape
        rgb = np.zeros((h_m, w_m, 3), dtype=np.uint8)
        # Fundo da mesa de impressão (grelha escura)
        rgb[:, :] = (12, 18, 32)
        # Sombra projetada da placa e dos furos
        s_shift = np.zeros_like(s_mask)
        s_shift[6:, 6:] = s_mask[:-6, :-6]
        shadow = s_shift & (~s_mask)
        rgb[shadow] = (3, 6, 12)

        # Corpo base da placa (Z = 0..2.0 mm): Antracite metálico escuro
        rgb[s_mask] = (28, 38, 56)

        # Borda biselada 3D na base
        edge_light = s_mask & (~np.roll(s_mask, 2, axis=0) | ~np.roll(s_mask, 2, axis=1))
        rgb[edge_light] = (65, 95, 135)

        # Sombra lateral do alto-relevo das letras (Z = 2.0..2.8 mm)
        r_shadow = np.roll(r_mask, 2, axis=0) & np.roll(r_mask, 2, axis=1) & (~r_mask) & s_mask
        rgb[r_shadow] = (12, 18, 28)

        # Topo do alto-relevo (+0.8 mm): Filamento Ciano/Branco Brilhante
        rgb[r_mask] = (0, 235, 255)
        r_highlight = r_mask & (~np.roll(r_mask, 1, axis=0))
        rgb[r_highlight] = (230, 255, 255)

        img = Image.fromarray(rgb, mode="RGB")
        return img.resize(target_size, Image.Resampling.LANCZOS)

    # Renderizar Placa 1 (Faceplate com furos) à esquerda
    p1_img = _render_shaded_plate(solid_mask, relief_mask, (980, 832))
    prev.paste(p1_img, (50, 190))
    p_draw.rounded_rectangle([50, 190, 50 + 980, 190 + 832], radius=12, outline=(0, 200, 255), width=2)
    p_draw.text(
        (55, 142),
        f"1. PLACA COM FUROS PARA A BASE (warthog_throttle_placa_base_3d.stl — 146x124x2.8 mm, {tris_faceplate:,} tris)",
        font=_get_font(18, bold=True),
        fill=(0, 255, 160),
    )

    # Renderizar Placa 2 (Quadro completo Base + Punhos) à direita
    p2_img = _render_shaded_plate(b_solid, b_relief, (1060, 752))
    prev.paste(p2_img, (1090, 230))
    p_draw.rounded_rectangle([1090, 230, 1090 + 1060, 230 + 752], radius=12, outline=(0, 200, 255), width=2)
    p_draw.text(
        (1095, 142),
        f"2. QUADRO COMPLETO PUNHOS + BASE (warthog_manete_dupla_quadro_3d.stl — 200x142x2.4 mm, {tris_board:,} tris)",
        font=_get_font(18, bold=True),
        fill=(255, 180, 0),
    )

    p_draw.text(
        (50, 1060),
        "PARÂMETROS RECOMENDADOS NO SLICER:  Altura de Camada: 0.20 mm  •  Bico: 0.4 mm  •  Infill: 20% Gyroid  •  Suportes: Não necessita (0 suportes)",
        font=_get_font(20, bold=True),
        fill=(180, 220, 255),
    )
    p_draw.text(
        (50, 1100),
        "TROCA DE COR (FILAMENTO DUPLO):  Placa 1 -> Trocar cor aos 2.00 mm (Camada 11)   |   Placa 2 -> Trocar cor aos 1.60 mm (Camada 9)",
        font=_get_font(20, bold=True),
        fill=(0, 240, 255),
    )

    preview_png_path.parent.mkdir(parents=True, exist_ok=True)
    prev.save(preview_png_path, "PNG", optimize=True)

    return {
        "faceplate_triangles": tris_faceplate,
        "board_triangles": tris_board,
    }


def generate_all_warthog_3d_and_diagrams(out_dir: Path) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    diagram_png = out_dir / "warthog_manete_dupla_sc_mapa.png"
    stl_faceplate = out_dir / "warthog_throttle_placa_base_3d.stl"
    stl_board = out_dir / "warthog_manete_dupla_quadro_3d.stl"
    svg_plate = out_dir / "warthog_throttle_placa_1para1.svg"
    preview_png = out_dir / "warthog_throttle_placa_3d_preview.png"

    generate_dual_throttle_annotated_diagram(diagram_png)
    stats = generate_3d_printable_throttle_plates(
        stl_faceplate_path=stl_faceplate,
        stl_board_path=stl_board,
        svg_path=svg_plate,
        preview_png_path=preview_png,
    )
    return {
        "diagram_png": str(diagram_png),
        "stl_faceplate": str(stl_faceplate),
        "stl_board": str(stl_board),
        "svg_plate": str(svg_plate),
        "preview_png": str(preview_png),
        "faceplate_triangles": str(stats["faceplate_triangles"]),
        "board_triangles": str(stats["board_triangles"]),
    }


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent / "profiles"
    res = generate_all_warthog_3d_and_diagrams(base_dir)
    for k, v in res.items():
        print(f"{k}: {v}")
