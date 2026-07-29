# Spec-Driven Research

Lee esta documentación en [English](README.md). Las guías en inglés y español
se mantienen bajo los mismos checks de paridad semántica.

Spec-Driven Research (SDR) es una CLI local que transforma una pregunta abierta
de investigación en evidencia revisable y una decisión explícita. Cada
investigación sigue un ciclo fijo, debe superar validaciones sobre sus artefactos
y deja registro cuando cambia la evidencia. Está pensada para equipos que
necesitan investigación aplicada repetible, no una carpeta desordenada de notas.

## Qué resuelve SDR

SDR ayuda a un equipo a:

- formular una pregunta falsable y criterios medibles antes de investigar;
- separar la exploración basada en fuentes de la validación ejecutable;
- conservar evidencia, limitaciones, revisiones humanas y decisiones de retroceso;
- producir un memo de decisión y un activo reutilizable antes del cierre;
- ofrecer resultados JSON determinísticos a personas, scripts y agentes de código.

SDR no es una base de datos fuente de verdad, un crawler web, un runtime de
agentes ni una garantía de veracidad de las fuentes citadas. Valida la estructura
declarada y la evidencia local. Las personas siguen siendo responsables de la
calidad de las fuentes, la ejecución segura y la recomendación final.

## Requisitos e instalación

SDR requiere Python 3.12 o posterior.

Instala el checkout como herramienta aislada con `uv`:

```bash
uv tool install .
sdr --help
```

Para desarrollar el proyecto, crea el entorno bloqueado:

```bash
uv sync --all-extras --dev
uv run sdr --help
```

También puedes instalar el checkout con `pip`:

```bash
python -m pip install .
sdr --help
```

La extracción de snapshots es opcional. Desde un checkout se instala con
`python -m pip install '.[snapshot]'`.

## Inicio rápido

Ejecuta estos pasos dentro de un repositorio Git. Por defecto, las transiciones
del ciclo crean commits acotados. Agrega `--no-commit` a los comandos que cambian
estado cuando no quieras ese efecto.

```bash
sdr new example-study \
  --title "Evaluate a data export approach" \
  --question "Which approach meets the stated reliability and maintenance criteria?" \
  --mode full \
  --no-commit
```

Edita `research/example-study/brief.md` sin alterar su frontmatter ni las
secciones obligatorias. Después valida y consulta la salida estructurada:

```bash
sdr check example-study --json
sdr advance example-study --no-commit
sdr status example-study --json
```

En cada etapa posterior, completa el artefacto generado, ejecuta la verificación
específica cuando corresponda, corre `check` y luego `advance`. La
[guía del workflow](docs/workflow.md) muestra el recorrido completo.

## Ciclo y modos

Las cinco etapas son:

| Etapa | Propósito | Evidencia principal |
| --- | --- | --- |
| `intake` | Definir pregunta, hipótesis, alcance, criterios y riesgos de adopción. | `brief.md` |
| `explore` | Comparar alternativas con fuentes fechadas, clasificadas y trazables. | `notes/*.md` y snapshots |
| `probe` | Probar los criterios con código o comandos reproducibles. | `probe/results.md` y artefactos de `probe/` |
| `transfer` | Recomendar una decisión respaldada por evidencia para una audiencia definida. | `decision-memo.md` |
| `reuse` | Empaquetar al menos un resultado reutilizable. | `assets/*.md` |

El modo full recorre `intake -> explore -> probe -> transfer -> reuse -> done`.
El modo light recorre `intake -> explore -> transfer -> reuse -> done`. Light
omite `probe`, pero no vuelve opcional a `reuse`. Usa full cuando necesites una
prueba ejecutable.

## Controles de validación

SDR presenta los controles según este orden conceptual de evidencia:
**Estructural**, **Evidential**, **Anclaje textual**, **Ejecutable**,
**Consistencia de hashes** y aprobación **HITL**. Antes de ejecutar los controles
de la etapa actual y cambiar el estado, `advance` comprueba la consistencia de
los hashes almacenados.

| Control | Comando | Etapa | ¿Bloquea `advance`? | Qué establece |
| --- | --- | --- | --- | --- |
| Estructural | `sdr check` | Todas | Sí | Existen los archivos, frontmatter, secciones y reglas de etapa obligatorios. |
| Evidential | `sdr check` | Principalmente explore/probe/transfer | Sí | Fuentes, referencias a criterios, artefactos y política de enlaces cumplen reglas determinísticas. |
| Anclaje textual | `sdr verify-claims` | Explore | Sí | Los claims factuales `[S<n>]` coinciden con snapshots locales vigentes o tienen una resolución humana explícita. |
| Ejecutable | `sdr verify-probe` | Probe | Sí | El comando declarado terminó bien, coincidió con `verify.expect` y conserva un hash vigente. |
| Consistencia de hashes | `sdr advance` y reporte de consistencia de `sdr check` | Etapas ya validadas | Sí | Los artefactos validados no cambiaron silenciosamente. |
| HITL | `sdr approve` | Transfer | Sí | Una persona aprobó el memo de decisión vigente. |
| Context Graph | `sdr context ...` | Cualquiera | No | Cobertura, relaciones, exports y consultas determinísticas auxiliares; no es trazabilidad completa. |

`check` ejecuta el gate estructural y evidencial para una etapa. Puede capturar
snapshots faltantes de explore salvo que se use `--offline`, pero nunca avanza
la etapa. `advance` coordina los controles bloqueantes, guarda el hash de
validación, cambia la etapa y puede crear un commit. `verify-claims` y
`verify-probe` producen evidencia explícita; `advance` no ejecuta comandos del
probe. `approve` registra una decisión humana, no un puntaje automático.

`[cf. S<n>]` es una referencia contextual. Valida la fuente declarada, pero no
crea un claim ni entra al matching textual. El anclaje textual no usa modelos.
`resolve-claim` registra una revisión humana acotada a la identidad vigente de un
claim; no reemplaza ni sustituye a `approve` en transfer.

El modo offline omite los checks de red y la captura automática de snapshots.
Los checks omitidos se reportan como omitidos, no aprobados. El matching textual
sigue necesitando snapshots locales existentes:

```bash
uv run sdr check example-study --offline
```

El Context Graph es opcional y no bloqueante. Resume relaciones seleccionadas,
pero no representa trazabilidad completa ni es requisito para `advance`. Consulta
[Modelo de evidencia](docs/evidence-model.md) y [Validación](docs/validation.md).

## Resumen de comandos

| Objetivo | Comandos | Modifica archivos o estado | Red | Git por defecto |
| --- | --- | --- | --- | --- |
| Crear trabajo | `sdr new` | Sí | No | Commit salvo `--no-commit` |
| Validar una etapa | `sdr check` | Puede capturar snapshots de explore | Checks de enlaces y captura salvo offline | No |
| Capturar y anclar fuentes | `sdr snapshot`, `sdr verify-claims`, `sdr resolve-claim` | Sí | `sdr snapshot` usa la red | No |
| Ejecutar un probe | `sdr verify-probe` | Ejecuta un proceso y guarda metadatos del resultado | Depende del comando | No |
| Avanzar o retroceder | `sdr advance`, `sdr reopen`, `sdr drop` | Sí | `sdr advance` puede comprobar enlaces | Commit salvo `--no-commit` |
| Aprobar transfer | `sdr approve` | Sí | Checks de enlaces opcionales | No |
| Reportar | `sdr status`, `sdr index`, `sdr doctor` | `sdr index` escribe `research/INDEX.md` | No | No |
| Consolidar | `sdr archive` | Escribe `knowledge/<slug>.md` | No | Commit salvo `--no-commit` |
| Grafo auxiliar | `sdr context build/inspect/trace/check/export/query` | Build/export escriben archivos derivados | No | No |
| Migrar metadatos legacy | `sdr migrate` | Sí | Captura fuentes declaradas | No |

Usa `--json` donde esté disponible para obtener una salida estructurada estable.
La [referencia de la CLI](docs/cli-reference.md) enumera todas las opciones,
guards y efectos secundarios.

## Ejecución de probes

La verificación del probe debe declarar `verify.action: run` y `verify.expect`
en `probe/results.md`. Es preferible usar una lista `argv`:

```yaml
verify:
  action: run
  argv: ["python", "verify.py"]
  expect: "PASS"
  environment: clean
```

SDR ejecuta `argv` directamente, sin un shell, usando `probe/` como directorio
de trabajo. Un string legacy `command` se separa en argumentos y también se
ejecuta sin un shell. Esto impide la expansión del shell, pero no vuelve seguro
al ejecutable. Revisa cada probe y prefiere `environment: clean`.

## Archivo y reapertura

`sdr archive <slug>` acepta únicamente investigaciones `done` o `dropped`,
escribe un artefacto conciso de conocimiento y marca la investigación como
archivada. `sdr reopen <slug> --to <stage> --reason <text>` solo retrocede,
registra el motivo, invalida los hashes afectados y puede reactivar trabajo
en estado `done`.

Ambos comandos crean commits de transición por defecto. Usa `--no-commit` cuando
el operador, el sistema de CI o el agente anfitrión administren el historial Git.

## Integraciones con agentes

La distribución instalada incluye recursos de paquete para Claude Code, Codex y
OpenCode. Instala las siete skills canónicas en el directorio de descubrimiento
del proyecto con:

```bash
sdr integrations install --destination PATH_TO_SKILLS
```

| Agente | Destino del proyecto | Estado actual |
| --- | --- | --- |
| Claude Code | `.claude/skills` | `documented` |
| Codex | `.agents/skills` | `documented` |
| OpenCode | `.opencode/skills` | `documented` |

El instalador copia recursos de skills equivalentes byte por byte desde el
paquete SDR instalado; no depende de rutas del checkout. `SDR_ROOT` controla
únicamente el almacenamiento de investigación y no es una fuente de integración
ni un destino de instalación.

`documented` significa que existen instrucciones de descubrimiento y checks
determinísticos del adaptador, pero no se registró un E2E completo con el host.
`verified` exige evidencia registrada y compatible por versión del
descubrimiento E2E del host y del ciclo con la CLI instalada. `experimental`
identifica un contrato incompleto o provisional. Los tres adaptadores actuales
permanecen en estado `documented`; ninguno afirma tener un E2E verificado con el
host. Consulta [Integraciones](docs/integrations.md).

## Seguridad y limitaciones

Trata notas, snapshots, repositorios, URLs, comandos de probe y cambios Git
generados como límites de confianza independientes. SDR bloquea destinos HTTP no
públicos, limita redirects y tamaño de snapshots, ejecuta probes sin un shell y
no hereda variables de proxy en su propio cliente HTTP. Estos controles no
demuestran que una fuente sea verdadera, no impiden que un ejecutable elegido
actúe de forma maliciosa, no detectan todas las credenciales ni crean un sandbox
para el host.

Mantén las credenciales fuera de los artefactos de investigación. Revisa los
comandos antes de ejecutarlos, inspecciona los archivos generados antes de
publicarlos y usa entornos con privilegios mínimos. Lee el
[Modelo de seguridad](docs/security-model.md) y [SECURITY.md](SECURITY.md).

## Contribuir

[CONTRIBUTING.md](CONTRIBUTING.md) describe los requisitos de OpenSpec, TDD,
calidad y contenido público. Quienes contribuyan mediante agentes también deben
seguir [AGENTS.md](AGENTS.md). Los checks de mantenimiento están en
[docs/validation.md](docs/validation.md).

## Licencia

Licenciado bajo Apache License 2.0. Consulta [LICENSE](LICENSE).
