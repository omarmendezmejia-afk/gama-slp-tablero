"""Registra el corte semanal (viernes) en ventas/semanal.json del repo gama-slp-tablero.

El tablero "Ventas, Cobranza y Metas" (ventas/ en el repo) lee ese archivo para la pestaña
"Cumplimiento semanal": ventas y cobrado acumulados del mes al corte vs la meta del mes.

SLP (después de calc.py del reporte semanal SLP):
  python3 registrar_corte.py --repo <checkout gama-slp-tablero> --slp data.json --corte 2026-11-06
QRO (después de generar_reporte_qro.py ... --json datos_qro.json):
  python3 registrar_corte.py --repo <checkout gama-slp-tablero> --qro datos_qro.json

Si ya existe un corte con la misma fecha para esa sucursal, lo reemplaza.
"""
import argparse, json
from pathlib import Path

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]


def corte_slp(path, corte):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    anio, mes = int(corte[:4]), int(corte[5:7])
    m = d.get(MESES[mes - 1]) or d.get(MESES[mes - 1].capitalize())
    if not m:
        raise SystemExit(f"data.json no trae el mes {MESES[mes - 1]}")
    return "san_luis", dict(anio=anio, mes=mes, corte=corte, ventas=round(m["ventas"], 2), cobrado=round(m["cobrado"], 2))


def corte_qro(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    nombre, anio = d["mes"].lower().split()   # mes comercial QRO, p. ej. "Noviembre 2026" = 25 oct a 24 nov
    t = d["total"]
    return "queretaro", dict(anio=int(anio), mes=MESES.index(nombre) + 1, corte=d["corte"],
                             ventas=round(t["ventas"], 2), cobrado=round(t["pagado"] + t.get("parcial", 0), 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--slp")
    ap.add_argument("--qro")
    ap.add_argument("--corte", help="fecha de corte AAAA-MM-DD (solo SLP)")
    a = ap.parse_args()
    if bool(a.slp) == bool(a.qro):
        raise SystemExit("Usa --slp o --qro")
    if a.slp and not a.corte:
        raise SystemExit("--slp necesita --corte")
    bu, reg = corte_slp(a.slp, a.corte) if a.slp else corte_qro(a.qro)
    f = Path(a.repo) / "ventas" / "semanal.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    lista = [c for c in data.get(bu, []) if c["corte"] != reg["corte"]] + [reg]
    data[bu] = sorted(lista, key=lambda c: c["corte"])
    f.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{bu}: corte {reg['corte']} ({MESES[reg['mes'] - 1]} {reg['anio']}) ventas {reg['ventas']:,.2f} cobrado {reg['cobrado']:,.2f}")


if __name__ == "__main__":
    main()
