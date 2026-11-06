"""Genera las figuras del informe ejecutivo a partir del dataset limpio."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import PercentFormatter

BASE = Path(__file__).resolve().parent
DATA = BASE.parent / "data" / "covid_us_clean.csv"
FIG_DIR = BASE / "figuras"

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 5)
plt.rcParams["savefig.dpi"] = 160

df = pd.read_csv(DATA, parse_dates=["fecha"])
df["estado"] = df["estado"].astype("category")
df = df.sort_values(["estado", "fecha"]).reset_index(drop=True)

FIG_DIR.mkdir(parents=True, exist_ok=True)

# 04. Evolución diaria y media móvil
diario = (
    df.groupby("fecha", as_index=False)
    .agg(casos_nuevos=("casos_nuevos", "sum"))
    .sort_values("fecha")
)
diario["casos_media_7d"] = diario["casos_nuevos"].rolling(7, min_periods=1).mean()

fig, ax = plt.subplots(figsize=(11, 4.5))
sns.lineplot(
    data=diario, x="fecha", y="casos_nuevos", color="lightcoral",
    alpha=0.45, label="Casos nuevos (diario)", ax=ax,
)
sns.lineplot(
    data=diario, x="fecha", y="casos_media_7d", color="firebrick",
    linewidth=2.2, label="Media móvil 7 días", ax=ax,
)
ax.set_title("Casos nuevos diarios y media móvil de 7 días")
ax.set_xlabel("Fecha")
ax.set_ylabel("Casos nuevos")
ax.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "04_evolucion_media_movil.png", bbox_inches="tight")
plt.close(fig)

# 05. Casos nuevos por mes
mensual = (
    df.assign(periodo=df["fecha"].dt.to_period("M").astype(str))
    .groupby("periodo", as_index=False)
    .agg(casos_nuevos=("casos_nuevos", "sum"))
    .sort_values("periodo")
)

fig, ax = plt.subplots(figsize=(10, 4.5))
sns.barplot(data=mensual, x="periodo", y="casos_nuevos", color="steelblue", ax=ax)
ax.set_title("Casos nuevos por mes en Estados Unidos")
ax.set_xlabel("Mes")
ax.set_ylabel("Casos nuevos")
ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.savefig(FIG_DIR / "05_casos_por_mes.png", bbox_inches="tight")
plt.close(fig)

# Resumen por estado y ratios
resumen = (
    df.groupby("estado", observed=True)
    .agg(
        casos_totales=("casos_positivos", "max"),
        fallecimientos_totales=("fallecimientos", "max"),
        pruebas_totales=("pruebas_totales", "max"),
    )
    .reset_index()
)
resumen["positividad"] = resumen["casos_totales"] / resumen["pruebas_totales"]
resumen["tasa_letalidad"] = resumen["fallecimientos_totales"] / resumen["casos_totales"]

# 06. Top 10 positividad
top_pos = (
    resumen.nlargest(10, "positividad")
    .sort_values("positividad")
    .assign(estado=lambda d: d["estado"].astype(str))
)

fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(data=top_pos, x="positividad", y="estado", color="darkorange", ax=ax)
ax.set_title("10 estados con mayor positividad acumulada")
ax.set_xlabel("Casos positivos / pruebas totales")
ax.set_ylabel("Estado")
ax.xaxis.set_major_formatter(PercentFormatter(1.0))
plt.tight_layout()
plt.savefig(FIG_DIR / "06_top_positividad.png", bbox_inches="tight")
plt.close(fig)

# 07. Matriz de correlación
ultimo = df.sort_values("fecha").groupby("estado", observed=True).tail(1).copy()
ultimo["ratio_positividad"] = (
    ultimo["casos_positivos"] / ultimo["pruebas_totales"].replace(0, np.nan)
)
ultimo["tasa_letalidad"] = (
    ultimo["fallecimientos"] / ultimo["casos_positivos"].replace(0, np.nan)
)

etiquetas = {
    "casos_positivos": "Casos positivos",
    "pruebas_totales": "Pruebas totales",
    "fallecimientos": "Fallecimientos",
    "hospitalizados_actuales": "Hospitalizados",
    "ratio_positividad": "Positividad",
    "tasa_letalidad": "Letalidad",
}
cols = list(etiquetas)
corr = ultimo[cols].corr().rename(index=etiquetas, columns=etiquetas)

fig, ax = plt.subplots(figsize=(7, 5.5))
sns.heatmap(
    corr, annot=True, fmt=".2f", cmap="coolwarm",
    vmin=-1, vmax=1, square=True, ax=ax,
)
ax.set_title("Matriz de correlación (último registro por estado)")
plt.tight_layout()
plt.savefig(FIG_DIR / "07_matriz_correlacion.png", bbox_inches="tight")
plt.close(fig)

# 08. Outliers con la regla del IQR
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
for ax, col in zip(axes, ["casos_nuevos", "fallecimientos_nuevos", "pruebas_nuevas"]):
    sns.boxplot(y=df[col], color="steelblue", ax=ax)
    ax.set_title(col.replace("_", " ").capitalize())
    ax.set_ylabel("")
fig.suptitle("Valores atípicos en los incrementos diarios (regla del IQR)")
plt.tight_layout()
plt.savefig(FIG_DIR / "08_outliers_iqr.png", bbox_inches="tight")
plt.close(fig)

print("Figuras generadas en", FIG_DIR)
