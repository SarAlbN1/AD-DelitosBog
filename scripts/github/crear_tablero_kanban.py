# -*- coding: utf-8 -*-
"""Crea (o actualiza) el tablero Kanban del backlog y lo vincula al repositorio.

GitHub solo permite vincular a un repositorio los proyectos de su MISMO dueño. Como el
repositorio pertenece a SarAlbN1, este script debe ejecutarlo Sara con su cuenta:

    gh auth login                 # si no ha iniciado sesión
    gh auth refresh -s project    # concede el permiso 'project' a gh
    python scripts/github/crear_tablero_kanban.py

Es idempotente: si el proyecto ya existe, solo añade los issues que falten y actualiza los campos.
Los valores se derivan de los issues:
  Status      -> cerrado: Done · PR abierto: In Review · etiqueta estado:bloqueado: Blocked ·
                 lista ESTADO_INICIAL · resto: Backlog (un estado puesto a mano en el tablero no se sobrescribe)
  Prioridad   -> etiqueta prioridad:*
  Entrega     -> milestone
  Estimación  -> fila «Estimación» del cuerpo del issue
"""
import argparse
import json
import re
import subprocess
import sys

TITULO = "AD-DelitosBog — Backlog"
ESTADOS = [("Backlog", "GRAY"), ("To Do", "BLUE"), ("In Progress", "YELLOW"), ("In Review", "PURPLE"),
           ("Blocked", "RED"), ("Done", "GREEN")]
CAMPOS = {"Prioridad": ["Crítica", "Alta", "Media", "Baja"],
          "Entrega": ["Entrega 1", "Entrega 2", "Entrega 3 / final"],
          "Estimación": ["S (≈2 h)", "M (≈4–6 h)", "L (≈8–12 h)"]}
PRIORIDAD = {"prioridad:critica": "Crítica", "prioridad:alta": "Alta", "prioridad:media": "Media", "prioridad:baja": "Baja"}
# Estado inicial acordado al publicar el backlog (2026-11-11)
ESTADO_INICIAL = {"To Do": [1, 2, 3, 5, 8, 9, 10, 11, 17, 23, 24], "In Progress": [12, 13]}


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"Error en gh {' '.join(args[:3])}…\n{r.stderr}")
    return r.stdout


def gql(query):
    return json.loads(gh("api", "graphql", "-f", f"query={query}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="SarAlbN1/AD-DelitosBog")
    a = ap.parse_args()
    owner = a.repo.split("/")[0]
    yo = gh("api", "user", "--jq", ".login").strip()
    if yo != owner:
        sys.exit(f"Este script debe ejecutarlo '{owner}' (sesión actual: '{yo}'). "
                 f"GitHub no permite vincular un proyecto de otro usuario al repositorio.")

    proyectos = json.loads(gh("project", "list", "--owner", owner, "--format", "json", "--limit", "100"))["projects"]
    p = next((x for x in proyectos if x["title"] == TITULO), None)
    if p is None:
        p = json.loads(gh("project", "create", "--owner", owner, "--title", TITULO, "--format", "json"))
        print("Proyecto creado:", p["url"])
    num, pid = str(p["number"]), p["id"]

    campos = {f["name"]: f for f in json.loads(gh("project", "field-list", num, "--owner", owner, "--format", "json"))["fields"]}
    st = campos["Status"]
    if [o["name"] for o in st.get("options", [])] != [n for n, _ in ESTADOS]:
        opts = ",".join(f'{{name:"{n}",color:{c},description:""}}' for n, c in ESTADOS)
        gql(f'mutation{{updateProjectV2Field(input:{{fieldId:"{st["id"]}",singleSelectOptions:[{opts}]}})'
            f'{{projectV2Field{{... on ProjectV2SingleSelectField{{id}}}}}}}}')
    for nombre, opciones in CAMPOS.items():
        if nombre not in campos:
            gh("project", "field-create", num, "--owner", owner, "--name", nombre, "--data-type", "SINGLE_SELECT",
               "--single-select-options", ",".join(opciones))
    campos = {f["name"]: f for f in json.loads(gh("project", "field-list", num, "--owner", owner, "--format", "json"))["fields"]}

    def opcion(campo, valor):
        return next(o["id"] for o in campos[campo]["options"] if o["name"] == valor)

    existentes = {i["content"].get("url"): i for i in
                  json.loads(gh("project", "item-list", num, "--owner", owner, "--format", "json", "--limit", "500"))["items"]}
    issues = json.loads(gh("issue", "list", "-R", a.repo, "--state", "all", "--limit", "500",
                           "--json", "number,url,state,labels,milestone,body"))
    prs = json.loads(gh("pr", "list", "-R", a.repo, "--state", "open", "--json", "number,url"))
    inicial = {n: e for e, ns in ESTADO_INICIAL.items() for n in ns}

    for it in issues + [dict(pr, state="OPEN", labels=[], milestone=None, body="", es_pr=True) for pr in prs]:
        previo = existentes.get(it["url"])
        item = previo["id"] if previo else json.loads(gh("project", "item-add", num, "--owner", owner, "--url",
                                                         it["url"], "--format", "json"))["id"]
        etiquetas = {l["name"] for l in it["labels"]}
        if it["state"] != "OPEN":
            estado = "Done"
        elif it.get("es_pr"):
            estado = "In Review"
        elif "estado:bloqueado" in etiquetas:
            estado = "Blocked"
        elif previo and previo.get("status"):
            estado = None  # no sobrescribir un estado movido a mano en el tablero
        else:
            estado = inicial.get(it["number"], "Backlog")
        valores = {"Status": estado,
                   "Prioridad": next((PRIORIDAD[l] for l in etiquetas if l in PRIORIDAD), None)}
        ms = (it.get("milestone") or {}).get("title", "")
        valores["Entrega"] = next((o for o in CAMPOS["Entrega"] if ms.startswith(o.split(" /")[0])), None)
        m = re.search(r"\| Estimación \| (\w)", it.get("body") or "")
        valores["Estimación"] = next((o for o in CAMPOS["Estimación"] if m and o.startswith(m.group(1))), None)
        for campo, valor in valores.items():
            if valor:
                gh("project", "item-edit", "--project-id", pid, "--id", item, "--field-id", campos[campo]["id"],
                   "--single-select-option-id", opcion(campo, valor))
        print(f"#{it['number']}: {valores}")

    vinculado = gh("api", f"repos/{a.repo}", "--jq", ".node_id").strip()
    gql(f'mutation{{linkProjectV2ToRepository(input:{{projectId:"{pid}",repositoryId:"{vinculado}"}}){{repository{{id}}}}}}')
    print(f"\nListo: {p.get('url')} (vinculado a {a.repo}).")
    print("En la web: abra el proyecto → '+ New view' → Board, agrupado por Status.")


if __name__ == "__main__":
    main()
