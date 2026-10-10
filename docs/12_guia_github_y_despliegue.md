# 12 · Guía para subir el proyecto a GitHub y publicar la demo

## 1. Preparar el repositorio local

Antes de publicar, edita:

- `README.md`: línea **Autores** y la insignia `OWNER/REPO`.
- `LICENSE`: reemplaza `[Nombre(s) del equipo]` por los nombres reales (o cambia la licencia si tu institución lo requiere).

```bash
cd que-como
git init
git add .
git commit -m "Versión inicial de ¿Qué Como? (MVP con Gradio)"
git branch -M main
```

## 2. Crear el repositorio en GitHub

**Opción A — sitio web**

1. Entra a <https://github.com/new>.
2. Nombre sugerido: `que-como`. Descripción: *Plataforma para comparar restaurantes con evaluaciones respaldadas por transacciones (MVP en Python + Gradio).*
3. **No** marques «Add a README», «.gitignore» ni «license» (ya existen en el proyecto).
4. Copia la URL del repositorio y ejecuta:

```bash
git remote add origin https://github.com/TU_USUARIO/que-como.git
git push -u origin main
```

**Opción B — GitHub CLI**

```bash
gh auth login
gh repo create que-como --public --source=. --remote=origin --push
```

Al subirlo, la pestaña **Actions** ejecutará las pruebas automáticamente.

## 3. Configuración recomendada en GitHub

- **About** (engrane a la derecha): agrega descripción y *topics*: `python`, `gradio`, `ingenieria-de-software`, `restaurantes`, `grasp`, `uml`.
- **Settings → Branches**: protege `main` y exige que pase el flujo «Pruebas» antes de fusionar.
- **Issues**: crea uno por cada pendiente de la hoja de ruta del README.

## 4. Flujo de trabajo en equipo

```bash
git checkout -b feature/persistencia-sqlite
# ...cambios + pruebas...
pytest && ruff check .
git commit -m "Agrega repositorios SQLite"
git push -u origin feature/persistencia-sqlite
# Abrir un Pull Request en GitHub
```

Ver [`CONTRIBUTING.md`](../CONTRIBUTING.md) para las convenciones.

## 5. Publicar la demo en Hugging Face Spaces (gratis)

1. Crea una cuenta en <https://huggingface.co> y un **Space** nuevo con SDK **Gradio**.
2. Sube el contenido del proyecto (o conecta el Space con tu repositorio de GitHub).
3. Hugging Face instala `requirements.txt` y ejecuta `app.py` automáticamente.
4. Agrega al inicio del `README.md` del Space este encabezado (solo en el Space):

```yaml
---
title: ¿Qué Como?
emoji: 🍽️
colorFrom: yellow
colorTo: red
sdk: gradio
app_file: app.py
pinned: false
---
```

> ⚠️ La demo usa **inicio de sesión simulado** y **datos ficticios**. No permitas que personas reales capturen datos personales en ella (ver [10](10_cumplimiento_legal.md)).

## 6. Exponer la app temporalmente desde tu computadora

```python
# En app.py, solo para una demostración rápida:
demo.launch(theme=TEMA, css=CSS, share=True)
```

Gradio genera un enlace público temporal. No lo uses con datos reales.
