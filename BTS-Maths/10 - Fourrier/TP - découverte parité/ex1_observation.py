import numpy as np
import matplotlib.pyplot as plt

# ============================================================
#  Exercice 1 -- Observation graphique de la parite
# ============================================================

x = np.linspace(-2 * np.pi, 2 * np.pi, 1000)

# --- Fonctions a observer ---
def f1(x): return np.cos(x)          # paire
def f2(x): return np.sin(x)          # impaire
def f3(x): return x**2               # paire
def f4(x): return x**3               # impaire
def f5(x): return np.exp(x)          # ni paire ni impaire
def f6(x): return np.cos(x) + np.sin(x)  # ni paire ni impaire

fonctions = [
    (f1, "cos(x)",        "steelblue"),
    (f2, "sin(x)",        "crimson"),
    (f3, "x²",            "teal"),
    (f4, "x³",            "darkorange"),
    (f5, "exp(x)",        "purple"),
    (f6, "cos(x)+sin(x)", "olive"),
]

fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()

for ax, (f, nom, couleur) in zip(axes, fonctions):
    y = f(x)
    ax.plot(x, y, color=couleur, linewidth=2, label=f'f(x) = {nom}')
    ax.axhline(0, color='black', linewidth=0.8)
    ax.axvline(0, color='black', linewidth=0.8)
    # Symetrie axe vertical (paire) en pointilles
    ax.plot(-x, y, 'k--', linewidth=1, alpha=0.4, label='f(-x)')
    ax.set_title(f'f(x) = {nom}', fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-2*np.pi, 2*np.pi)

fig.suptitle("Observation graphique -- Fonctions paires et impaires", fontsize=13)
plt.tight_layout()
plt.savefig('ex1_observation.png', dpi=150)
plt.show()

# ============================================================
#  Axe de symetrie et centre de symetrie
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Fonction paire : symetrie par rapport a l'axe Oy
ax = axes[0]
ax.plot(x, f1(x), color='steelblue', linewidth=2, label='f(x) = cos(x)')
ax.fill_between(x[x >= 0], f1(x[x >= 0]), alpha=0.2, color='steelblue', label='x > 0')
ax.fill_between(x[x <= 0], f1(x[x <= 0]), alpha=0.2, color='orange',    label='x < 0')
ax.axvline(0, color='red', linewidth=1.5, linestyle='--', label='axe de symetrie')
ax.set_title("Fonction PAIRE : symetrie / axe Oy")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Fonction impaire : symetrie par rapport a l'origine
ax = axes[1]
ax.plot(x, f2(x), color='crimson', linewidth=2, label='f(x) = sin(x)')
ax.plot(0, 0, 'ko', markersize=8, label='centre de symetrie O')
ax.set_title("Fonction IMPAIRE : symetrie / origine O")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

fig.suptitle("Symetries caracteristiques", fontsize=13)
plt.tight_layout()
plt.savefig('ex1_symetries.png', dpi=150)
plt.show()
