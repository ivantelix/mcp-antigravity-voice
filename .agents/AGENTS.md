# Antigravity Agent Rules

### Regla Obligatoria para Text-to-Speech (TTS)
1. **Paso Final:** En cada interacción, tu último paso debe ser SIEMPRE invocar la herramienta `speak_message`.
2. **Planes de Implementación y Walkthroughs:** Al crear o actualizar un plan de implementación (`implementation_plan.md`) o un resumen de cambios (`walkthrough.md`), debes llamar a `speak_message` para leer en voz alta un resumen hablado claro (2 a 4 oraciones) que explique la meta principal, las decisiones clave y los próximos pasos.
3. **Anuncio de Permisos y Acciones Sensibles:** Antes de proponer la ejecución de comandos de consola o acceder a archivos fuera del workspace, debes llamar a `speak_message` para avisarle al usuario en voz alta: *"Señor, necesito su confirmación para [acceder al archivo X / ejecutar el comando Y]"*.
4. **Preguntas y Confirmaciones:** Si durante la ejecución necesitas pedirle confirmación, hacerle una pregunta o solicitar datos al usuario, debes llamar a `speak_message` para leer la pregunta en voz alta.
5. **Síntesis Conversacional:** NUNCA envíes bloques de código, comandos de consola o sintaxis técnica pesada a la herramienta `speak_message`. En su lugar, envía un resumen conversacional breve en español de lo realizado.
