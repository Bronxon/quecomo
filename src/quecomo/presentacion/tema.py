"""Identidad visual de ¿Qué Como?: «atardecer en el desierto».

Paleta naranja–azul inspirada en el cielo nocturno que se encuentra con el
horizonte al atardecer. El único elemento expresivo es el encabezado; el resto
de la interfaz es sobrio para que la información de los restaurantes destaque.

| Token       | Hex       | Uso                                         |
|-------------|-----------|---------------------------------------------|
| Noche       | #12203A   | Encabezado, títulos, texto principal        |
| Cobalto     | #2456A6   | Acciones secundarias, foco, enlaces         |
| Cielo       | #E8EEF8   | Superficies suaves, cabeceras de tabla      |
| Atardecer   | #F27A1A   | Acción principal, pestaña activa, controles |
| Brasa       | #C4580A   | Texto naranja sobre fondo claro (contraste) |
| Fondo       | #F5F7FB   | Fondo general                               |
"""

from __future__ import annotations

import gradio as gr

NOCHE = "#12203A"
COBALTO = "#2456A6"
CIELO = "#E8EEF8"
ATARDECER = "#F27A1A"
BRASA = "#C4580A"
FONDO = "#F5F7FB"

naranja = gr.themes.Color(
    name="atardecer",
    c50="#FFF4EB", c100="#FFE4CC", c200="#FFC799", c300="#FFA65C", c400="#FB8C33",
    c500=ATARDECER, c600="#D9660C", c700=BRASA, c800="#8F420C", c900="#74370E", c950="#3F1B05",
)
azul = gr.themes.Color(
    name="noche",
    c50="#EEF3FB", c100=CIELO, c200="#B9CDEC", c300="#8EADDF", c400="#5F88CC",
    c500="#3B6CB8", c600=COBALTO, c700="#1D4586", c800="#1A3868", c900=NOCHE, c950="#0B1426",
)

TEMA = gr.themes.Base(
    primary_hue=naranja,
    secondary_hue=azul,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Manrope"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("Manrope"), "ui-sans-serif", "system-ui", "sans-serif"],
    radius_size=gr.themes.sizes.radius_lg,
    spacing_size=gr.themes.sizes.spacing_md,
).set(
    # Fondo y texto
    body_background_fill=FONDO,
    body_background_fill_dark="#0D1626",
    body_text_color=NOCHE,
    body_text_color_dark="#E6ECF5",
    body_text_color_subdued="#5B6B86",
    # Bloques
    block_background_fill="#FFFFFF",
    block_background_fill_dark="#15213A",
    block_border_color="#E3E9F2",
    block_border_color_dark="#22314F",
    block_border_width="1px",
    block_shadow="0 1px 2px rgba(18, 32, 58, 0.04)",
    block_radius="14px",
    block_label_background_fill="transparent",
    block_label_background_fill_dark="transparent",
    block_label_text_color="#3C4C68",
    block_label_text_color_dark="#AFC0DB",
    block_label_text_weight="600",
    block_title_text_color=NOCHE,
    block_title_text_color_dark="#E6ECF5",
    block_title_text_weight="700",
    # Campos
    input_background_fill="#F8FAFD",
    input_background_fill_dark="#101B30",
    input_border_color="#D6DEEA",
    input_border_color_dark="#2A3B5C",
    input_border_color_focus=COBALTO,
    input_border_color_focus_dark="#6E9BE8",
    input_shadow_focus="0 0 0 3px rgba(36, 86, 166, 0.18)",
    # Botones
    button_primary_background_fill=ATARDECER,
    button_primary_background_fill_hover="#D9660C",
    button_primary_background_fill_dark=ATARDECER,
    button_primary_background_fill_hover_dark="#FB8C33",
    button_primary_text_color="#FFFFFF",
    button_primary_border_color=ATARDECER,
    button_secondary_background_fill="#FFFFFF",
    button_secondary_background_fill_hover=CIELO,
    button_secondary_background_fill_dark="#15213A",
    button_secondary_background_fill_hover_dark="#1D2C4A",
    button_secondary_text_color=COBALTO,
    button_secondary_text_color_dark="#9DBCF0",
    button_secondary_border_color="#B9CDEC",
    button_secondary_border_color_dark="#2A3B5C",
    button_cancel_background_fill="#FFFFFF",
    button_cancel_background_fill_hover="#FDECEC",
    button_cancel_text_color="#B42318",
    button_cancel_border_color="#F3C2BD",
    # Controles
    checkbox_background_color_selected=ATARDECER,
    checkbox_border_color_selected=ATARDECER,
    checkbox_label_background_fill_selected="#FFF4EB",
    checkbox_label_background_fill_selected_dark="#2A1E14",
    checkbox_label_border_color_selected=ATARDECER,
    checkbox_label_text_color_selected=BRASA,
    checkbox_label_text_color_selected_dark="#FFC799",
    slider_color=ATARDECER,
    color_accent=ATARDECER,
    color_accent_soft="#FFF4EB",
    color_accent_soft_dark="#2A1E14",
    link_text_color=COBALTO,
    link_text_color_dark="#9DBCF0",
    # Tablas
    table_border_color="#E3E9F2",
    table_even_background_fill="#FFFFFF",
    table_odd_background_fill="#F8FAFD",
    table_even_background_fill_dark="#15213A",
    table_odd_background_fill_dark="#121D33",
)

CSS = f"""
.gradio-container {{ max-width: 1240px !important; margin: 0 auto !important; }}
footer {{ display: none !important; }}

/* ---- Encabezado: el único elemento expresivo ---- */
#encabezado {{
  position: relative; overflow: hidden;
  border-radius: 22px; padding: 34px 36px 40px;
  background:
    radial-gradient(70% 95% at 82% 128%, #FFC07A 0%, {ATARDECER} 28%, rgba(242,122,26,.45) 46%,
                    rgba(242,122,26,0) 64%),
    linear-gradient(180deg, #0E1A31 0%, {NOCHE} 55%, #1A3868 100%);
  color: #fff;
}}
#encabezado::after {{
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 4px;
  background: linear-gradient(90deg, {COBALTO}, {ATARDECER});
}}
#encabezado .marca {{ display: flex; align-items: center; gap: 14px; }}
#encabezado h1 {{
  margin: 0; font-size: clamp(2rem, 4vw, 2.9rem); font-weight: 800;
  letter-spacing: -0.03em; line-height: 1.05; color: #fff;
}}
#encabezado p {{ margin: 12px 0 0; max-width: 46ch; font-size: 1.05rem; color: #D5DFEF; }}
#encabezado .aviso {{
  display: inline-block; margin-top: 16px; padding: 4px 12px; border-radius: 999px;
  font-size: .82rem; color: #FFE4CC; background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.16);
}}

/* ---- Barra de sesión ---- */
#sesion {{ margin-top: 4px; align-items: center; }}
#bienvenida {{ padding: 4px 6px; }}

/* ---- Pestañas: subrayado naranja, sin adornos ---- */
.tab-wrapper, [role="tablist"] {{ border-bottom: 1px solid #E3E9F2; gap: 4px; }}
button[role="tab"] {{
  font-weight: 600; color: #5B6B86; border: none !important; background: transparent !important;
  padding: 10px 14px; border-radius: 0 !important; position: relative;
}}
button[role="tab"]:hover {{ color: {NOCHE}; }}
button[role="tab"][aria-selected="true"] {{ color: {NOCHE}; }}
button[role="tab"][aria-selected="true"]::after {{
  content: ""; position: absolute; left: 10px; right: 10px; bottom: -1px; height: 3px;
  border-radius: 3px 3px 0 0; background: {ATARDECER};
}}
button[role="tab"]:focus-visible {{ outline: 2px solid {COBALTO}; outline-offset: 2px; }}

/* ---- Tablas legibles (sin fuente monoespaciada) ---- */
table, table * {{ font-family: var(--font) !important; }}
table {{ font-variant-numeric: tabular-nums; font-size: .92rem; }}
table thead th {{ background: {CIELO} !important; color: {NOCHE} !important; font-weight: 700 !important; }}

/* ---- Mensajes y textos ---- */
.mensaje p {{ font-size: 1rem; font-weight: 500; }}
.nota p, .nota {{ color: #5B6B86; font-size: .9rem; }}
h2, h3, h4 {{ letter-spacing: -0.01em; }}

/* ---- Modo oscuro ---- */
.dark .tab-wrapper, .dark [role="tablist"] {{ border-color: #22314F; }}
.dark button[role="tab"] {{ color: #8FA3C2; }}
.dark button[role="tab"][aria-selected="true"], .dark button[role="tab"]:hover {{ color: #FFFFFF; }}
.dark table thead th {{ background: #1D2C4A !important; color: #E6ECF5 !important; }}
.dark .nota p, .dark .nota {{ color: #8FA3C2; }}

@media (max-width: 640px) {{
  #encabezado {{ padding: 26px 20px 30px; border-radius: 16px; }}
  button[role="tab"] {{ padding: 8px 10px; }}
}}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
"""

# Marca: un sol a medio ocultarse en el horizonte.
_SOL = f"""
<svg width="44" height="44" viewBox="0 0 44 44" aria-hidden="true">
  <defs><clipPath id="horizonte"><rect x="0" y="0" width="44" height="28"/></clipPath></defs>
  <circle cx="22" cy="28" r="15" fill="{ATARDECER}" clip-path="url(#horizonte)"/>
  <rect x="4" y="31" width="36" height="3" rx="1.5" fill="#FFC799"/>
  <rect x="10" y="37" width="24" height="3" rx="1.5" fill="#8EADDF"/>
</svg>
"""

ENCABEZADO = f"""
<header id="encabezado">
  <div class="marca">{_SOL}<h1>¿Qué Como?</h1></div>
  <p>Encuentra, compara y elige dónde comer con reseñas de quienes realmente fueron.</p>
  <span class="aviso">Prototipo académico con datos ficticios</span>
</header>
"""
