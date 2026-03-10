# Agentic Migration Kit

Kit reutilizavel de migracao orientada a IA.

O kit vive apenas em `docs/java-agentic-migration-kit`.

O output de cada projeto vive apenas em `docs/java-migration`.

## Escopo do produto

Escopo suportado nesta versao:

- `v1` e `Maven-first`
- foco principal em repositorios Java e migracao `Java EE` -> `Jakarta EE`
- foco principal em repositorios com `mvn` ou `mvnw`
- foco principal em execucao por ondas pequenas e auditaveis

Fora de escopo por enquanto:

- automacao `Gradle-first`
- monorepos heterogeneos com multiplos build systems sem roteamento adicional
- migracoes genericas que nao sejam majoritariamente sobre baseline Java/Jakarta

Se o repositorio nao satisfaz esse escopo, o kit deve diagnosticar, persistir a
restricao e parar antes de entrar em automacao.

Ponto de entrada unico:

- `bootstrap/scripts/migration-kit.sh`
  use `start`, `resume` ou `status`

Skill principal para uso humano:

- `migration-orchestrator/`
  use esta skill primeiro para perguntas abertas de estrategia, atualizacao ou
  migracao

## Conteudo

- `bootstrap/`
  entrypoint e scripts internos de bootstrap e retomada
- `schemas/`
  contratos do estado e dos runs
- `scripts/`
  utilitarios reutilizaveis do kit, incluindo sincronizacao de escopos e
  resolucao de rota do estado
- `migration-orchestrator/`
  skill principal de entrada e controle do fluxo
- `migration-bootstrap/`
  skill especializada de bootstrap, normalmente acionada pelo orquestrador
- `migration-discovery/`
  skill especializada para baseline e discovery por escopo
- `migration-openrewrite/`
  skill especializada e scripts para automacao via `OpenRewrite`
- `migration-transformer-fallback/`
  skill especializada de excecao para `Eclipse Transformer`
- `migration-wave-planner/`
  skill especializada para sequenciar ondas
- `migration-last-mile-fixer/`
  skill especializada para corrigir residual apos automacao

## Como usar

Distribuicao prevista:

- o destino correto deste produto e empacotamento como skill do Codex em
  `$CODEX_HOME/skills` ou `~/.codex/skills`
- este repositorio mantem a implementacao-fonte do kit
- `docs/java-agentic-migration-kit` nao deve ser tratado como pacote copiavel
  via scripts locais de install/uninstall
- a unidade instalavel de menor risco e `migration-orchestrator/` como skill
  principal autocontida
- caminhos legados fora de `migration-orchestrator/` permanecem nesta etapa
  apenas para compatibilidade e revisao

Comece por `migration-orchestrator` quando quiser perguntar, por exemplo:

- "como atualizar essa codebase?"
- "qual a estrategia de atualizacao desse projeto?"
- "como migrar este projeto para jakarta?"
- "quero atualizar esse projeto javaee para jakartaee"

O `migration-orchestrator` deve tratar esses pedidos em tres modos principais:

- estrategia de atualizacao
- diagnostico de migracao para Jakarta
- execucao inicial da migracao

## Formato de skill

Formato alvo para empacotamento:

- `migration-orchestrator/SKILL.md`
- `migration-orchestrator/agents/openai.yaml`
- `migration-orchestrator/scripts/`
- `migration-orchestrator/references/`

Nesta revisao:

- `migration-orchestrator/` concentra o bundle instalavel
- `bootstrap/`, `scripts/` e subskills legadas continuam presentes sem remocao
  destrutiva

## Regras do kit

- `docs/java-agentic-migration-kit` contem apenas ferramenta reutilizavel.
- `docs/java-migration` contem apenas output do projeto atual.
- `migration-orchestrator` e a skill principal de entrada.
- As demais skills sao operadas pelo orquestrador.
- Toda retomada deve depender de estado em disco, nao da conversa anterior.
- Tudo que for repetivel e deterministico deve morar em scripts, presets ou schemas.
- O kit nao deve guardar historico de conversa, decisoes locais desta sessao ou
  artefatos especificos de um repositorio dentro da propria area reutilizavel.
- O orquestrador deve declarar quando esta apenas em modo consultivo e quando
  esta autorizado a avancar estado.
- Nenhuma fase deve avancar sem pre-condicoes explicitas no estado oficial.

## Output minimo da primeira execucao

O bootstrap deve deixar, no minimo:

- `docs/java-migration/README.md`
- `docs/java-migration/adr/adr-001-target-stack.md`
- `docs/java-migration/adr/adr-002-migration-strategy.md`
- `docs/java-migration/milestones/milestone-0-discovery.md`
- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/state/session-handoff.md`
- `docs/java-migration/discovery-protocol/manifests/scopes.csv`
- `docs/java-migration/discovery-protocol/runs/`
- `docs/java-migration/openrewrite-runs/`

## Roteamento por fase

O estado oficial fica em:

- `docs/java-migration/state/project.state.json`
- `docs/java-migration/state/active-milestone.json`
- `docs/java-migration/state/session-handoff.md`

O orquestrador deve tratar o fluxo assim:

- `bootstrap_governance` -> `migration-bootstrap`
- `structured_discovery` -> `migration-discovery`
- `migration_planning` -> `migration-wave-planner`
- `automated_execution` -> `migration-openrewrite`
- `last_mile_fixes` -> `migration-last-mile-fixer`
- excecao explicita -> `migration-transformer-fallback`

## Modos do orquestrador

O orquestrador deve operar com um modo explicito, persistido no estado:

- `assess`
  responder estrategia ou diagnostico sem executar migracao
- `bootstrap`
  inicializar o output oficial
- `discover`
  produzir baseline e evidencias por escopo
- `plan`
  montar ondas executaveis
- `execute`
  rodar automacao segura e pequena
- `stabilize`
  consumir residual apos automacao
- `resume`
  retomar a partir do estado oficial

Regra de ouro:

- a intencao do usuario ajuda a escolher o modo inicial
- o estado persistido e as pre-condicoes validas mandam na fase seguinte
