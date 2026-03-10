# Maven OpenRewrite Notes

## Objetivo

Guiar a execucao de `OpenRewrite` em repositorios Maven com batches pequenos e
revisaveis.

## Uso recomendado

- aplicar recipes por escopo, nao no monorepo inteiro de uma vez;
- usar `dryRun` antes do `run` sempre que o impacto ainda for desconhecido;
- registrar cada batch em `docs/java-migration/openrewrite-runs/<run-id>/`;
- validar o build dos escopos afetados logo apos um `run` bem-sucedido;
- tratar `javax -> jakarta` como recipe set inicial, nao como unica etapa da
  migracao.

## Recipe set inicial

O runner deste kit atualmente materializa:

- `org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta`

Os presets ficam em:

- `presets/jakarta-ee.json`
- `presets/build-modernization.json`

Expansoes futuras podem adicionar recipe sets separados para:

- modernizacao de `pom.xml`;
- ajustes de plugins Maven;
- XMLs e descritores;
- upgrades de bibliotecas especificas.

## Leitura de resultados

Se o `dryRun` falhar com mudancas pendentes, isso nao significa problema no
build. Significa apenas que o recipe encontrou alteracoes propostas.

Depois de um `run` real, o kit valida Maven por escopo com `test-compile` por
padrao e grava `validation-summary.json` no mesmo diretório do run.

Se o `run` falhar:

- verificar incompatibilidades de plugin;
- verificar se o recipe exige dependencias adicionais;
- verificar se o escopo escolhido esta grande demais;
- empurrar o residual para `migration-last-mile-fixer` apenas depois de tentar
  refinar o batch.
