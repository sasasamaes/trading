#!/bin/bash
# Hook UserPromptSubmit: detecta palabras peligrosas y alerta

PROMPT_INPUT=$(cat)

# Palabras clave de auto-sabotaje
if echo "$PROMPT_INPUT" | grep -qiE "(arriesgar (todo|mucho)|all.in|aumentar leverage|saltar.*filtro|entrar sin|mover el sl|recuperar (rapido|rápido)|subir el leverage|más apalancamiento)"; then
    cat <<EOF >&2

⚠️ ═══ ALERTA DE AUTO-SABOTAJE ═══

Detecté lenguaje de riesgo elevado en tu prompt.

Recordatorio de reglas sagradas:
  • Max 2% riesgo por trade (regla matemática)
  • Nunca mover SL en dirección contraria
  • Nunca subir leverage arriba de 10x
  • Nunca saltarse los 4 filtros
  • Nunca operar para "recuperar" pérdidas

Si realmente quieres romper una regla, detente 5 minutos.
Pregúntate: ¿qué diría mi yo del mes pasado?

Este mensaje NO bloquea tu acción — solo te advierte.

══════════════════════════════

EOF
fi

exit 0
