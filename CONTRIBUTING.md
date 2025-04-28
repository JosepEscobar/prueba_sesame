### 📄 `CONTRIBUTING.md`

```markdown
# Guía de Contribución

¡Gracias por tu interés en contribuir a este proyecto!

Queremos mantener una base de código limpia, escalable y de alta calidad. Por favor, sigue las siguientes reglas para cualquier contribución:

## 🛠️ Cómo contribuir

1. **Clona el repositorio** y crea una nueva rama basada en `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/nombre-de-tu-feature
   ```

2. **Sigue el estilo de código**:
   - Formatea el código automáticamente con **Black**.
   - Asegúrate de que **Ruff** no reporte errores:
     ```bash
     ruff .
     black .
     ```

3. **Añade tests** si tu contribución agrega o cambia funcionalidades.
   - Ejecuta todos los tests locales antes de enviar tu PR:
     ```bash
     pytest
     ```

4. **Documenta tu contribución**:
   - Actualiza el README o añade comentarios si tu cambio impacta la funcionalidad existente o agrega nueva.

5. **Haz commits claros y descriptivos por cada funcionalidad que implementes**:
   - Usa mensajes de commit siguiendo el formato:
     ```
     feat: descripción de nueva funcionalidad
     fix: corrección de bug
     docs: cambios en la documentación
     chore: tareas internas (scripts, CI, etc.)
     ```

6. **Envía un Pull Request**:
   - Asegúrate que tu PR se dirige a la rama `develop`.
   - Describe claramente **qué problema soluciona** o **qué funcionalidad añade**.
   - Incluye capturas de pantalla o ejemplos si es aplicable.

## ✅ Criterios de aceptación de PRs

- Pasa todos los tests unitarios y de integración.
- Pasa el chequeo de linting y formateo.
- Cumple con los patrones de arquitectura del proyecto.
- No rompe la compatibilidad con otras partes del sistema.

## 🧹 Regla de Oro

> **Deja el código mejor de lo que lo encontraste.**

---

¡Gracias por ayudarnos a construir un proyecto mejor! 🚀


