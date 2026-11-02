#!/usr/bin/env bash
# Auditoria da presença de uma feature no Eclipse Simultaneous Release (simrel), release a release.
# Só usa comandos git de leitura no repositório simrel.build (github.com/eclipse-simrel/simrel.build).
#
# Uso:  ./presenca.sh <regex do arquivo de contribuição> [<nome da feature p2>]
#   ex.: ./presenca.sh '^birt\.(b3)?aggrcon$'
#        ./presenca.sh '^ep\.(b3)?aggrcon$' org.eclipse.cvs.feature.group     (CVS vinha dentro da contribuição do Platform)
#
# Para cada tag de release do simrel, em ordem cronológica, imprime:
#   tag | data do commit da tag | arquivo de contribuição | C1 arquivo existe | C2 referenciado no simrel.(b3)aggr |
#   C3 contribuição habilitada | C4 feature p2 presente (se informada) | update site (1º repositório)
# A feature é considerada PRESENTE na release quando C1, C2, C3 (e C4, se informada) são todos "sim".
set -u
SIMREL="${SIMREL:-$(dirname "$0")/../../simrel.build}"
PAT="$1"; FEAT="${2:-}"
g() { git -C "$SIMREL" "$@"; }

printf 'tag\tdata\tarquivo\tC1_existe\tC2_referenciado\tC3_habilitado\tC4_feature\tupdate_site\n'
# tags em ordem cronológica pela data do commit apontado (vale para tags anotadas e leves)
TAGS=$(for t in $(g tag); do echo "$(g show -s --format=%ct "$t^{commit}") $t"; done | sort -n | cut -d' ' -f2)
for tag in $TAGS; do
  date=$(g show -s --format=%cs "$tag^{commit}")
  file=$(g ls-tree --name-only "$tag^{commit}" | grep -E "$PAT" | head -1)
  if [ -z "$file" ]; then
    printf '%s\t%s\t-\tnao\t-\t-\t-\t-\n' "$tag" "$date"; continue
  fi
  main=$(g ls-tree --name-only "$tag^{commit}" | grep -E '^simrel\.(b3)?aggr$' | head -1)
  ref=$(g show "$tag:$main" | grep -q "href=\"$file#" && echo sim || echo nao)
  xml=$(g show "$tag:$file")
  # contribuição desabilitada = atributo enabled="false" na tag raiz <aggregator:Contribution ...>
  hab=$(echo "$xml" | tr '\n' ' ' | grep -oE '<aggregator:Contribution[^>]*>' | grep -q 'enabled="false"' && echo nao || echo sim)
  c4='-'
  if [ -n "$FEAT" ]; then
    line=$(echo "$xml" | grep -E "name=\"$FEAT\"" | head -1)
    if [ -z "$line" ]; then c4=nao; elif echo "$line" | grep -q 'enabled="false"'; then c4=desabilitada; else c4=sim; fi
  fi
  site=$(echo "$xml" | grep -oE 'location="[^"]+"' | head -1 | sed 's/location=//; s/"//g')
  printf '%s\t%s\t%s\tsim\t%s\t%s\t%s\t%s\n' "$tag" "$date" "$file" "$ref" "$hab" "$c4" "$site"
done
