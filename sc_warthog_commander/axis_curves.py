"""
Axis Curves & Exponential Filtering
Calcula curvas de resposta não-lineares (Exponencial e Curva-S) para compensar a mola pesada
do manche HOTAS Warthog e permitir micro-mira precisa no centro.
"""

import math

def apply_deadzone(normalized_val: float, deadzone: float) -> float:
    """
    Aplica a zona morta (deadzone 0.0 a 0.5) num valor normalizado (-1.0 a 1.0).
    Remove o ruído no centro e reescala suavemente o restante percurso.
    """
    if abs(normalized_val) <= deadzone:
        return 0.0
    sign = 1.0 if normalized_val > 0 else -1.0
    scaled = (abs(normalized_val) - deadzone) / (1.0 - deadzone)
    return sign * min(1.0, max(0.0, scaled))

def apply_curve(val: float, curve_type: str = "expo", exponent: float = 1.8) -> float:
    """
    Aplica uma curva de resposta:
    - 'linear': linear direto
    - 'expo': curva exponencial (|x|^exponent)
    - 's_curve': curva sigmoide suave
    """
    sign = 1.0 if val >= 0 else -1.0
    abs_val = abs(val)

    if curve_type == "linear":
        return val

    elif curve_type == "expo":
        return sign * math.pow(abs_val, exponent)

    elif curve_type == "s_curve":
        # Curva-S cúbica suave (Smoothstep)
        # f(x) = 3x^2 - 2x^3 combinada com expoente
        smooth = (3.0 * abs_val * abs_val) - (2.0 * abs_val * abs_val * abs_val)
        return sign * (0.5 * smooth + 0.5 * math.pow(abs_val, exponent))

    return val

def generate_curve_points(curve_type: str = "expo", exponent: float = 1.8, deadzone: float = 0.12, steps: int = 50) -> list[dict]:
    """Gera uma lista de pontos (x, y) de -1.0 a +1.0 para desenhar o gráfico SVG/Canvas no Dashboard."""
    points = []
    for i in range(steps + 1):
        x = -1.0 + (2.0 * i / steps)
        # Aplica deadzone e depois curva
        x_dz = apply_deadzone(x, deadzone)
        y = apply_curve(x_dz, curve_type, exponent)
        points.append({"x": round(x, 3), "y": round(y, 3)})
    return points
