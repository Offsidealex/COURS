import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad

# ============================================================
#  Exercice 4 -- Lien parite / coefficients de Fourier
#
#  Si f est PAIRE  => bn = 0 pour tout n
#  Si f est IMPAIRE => a0 = 0 et an = 0 pour tout n
# ============================================================

T = 2 * np.pi
x = np.linspace(0, 2 * T, 1000)
N_max = 10

# --- Calcul des coefficients ---
def calcul_a0(f, T):
    val, _ = quad(f, 0, T)
    return (2 / T) * val

def calcul_an(f, T, n):
    val, _ = quad(lambda x: f(x) * np.cos(2 * np.pi * n * x / T), 0, T)
    return (2 / T) * val

def calcul_bn(f, T, n):
    val, _ = quad(lambda x: f(x) * np.sin(2 * np.pi * n * x / T), 0, T)
    return (2 / T) * val

def afficher_coefficients(f, nom):
    a0 = calcul_a0(f, T)
    an = [calcul_an(f, T, n) for n in range(1, N_max + 1)]
    bn = [calcul_bn(f, T, n) for n in range(1, N_max + 1)]
    print(f"\n{'='*55}")
    print(f"  f(x) = {nom}")
    print(f"{'='*55}")
    print(f"  a0 = {a0:+.6f}")
    print(f"  {'n':>3} | {'a_n':>12} | {'b_n':>12}")
    print(f"  {'-'*3}-+-{'-'*12}-+-{'-'*12}")
    for n in range(1, N_max + 1):
        print(f"  {n:>3} | {an[n-1]:>+12.6f} | {bn[n-1]:>+12.6f}")
    return a0, an, bn

# ============================================================
#  Fonctions periodisees sur [0, 2pi]
# ============================================================

# Paire : cos(x)
def f_paire(x):
    return np.cos(x % T - np.pi)   # cosinus centre en pi -> symetrique

# Impaire : sin(x)
def f_impaire(x):
    return np.sin(x % T - np.pi)   # sinus centre en pi -> antisymetrique

# Ni paire ni impaire : exp(x) periodisee sur [0, T[
def f_quelconque(x):
    return np.exp(x % T)

# Paire explicite : triangle (de l'exercice Fourier)
def f_triangle(x):
    x_mod = x % T
    return np.abs(x_mod - np.pi) - np.pi / 2

# Impaire explicite : creneau (de l'exercice Fourier)
def f_creneau(x):
    x_mod = x % T
    return np.where(x_mod < np.pi, 1.0, -1.0)

# ============================================================
#  Affichage des coefficients
# ============================================================
a0_p,  an_p,  bn_p  = afficher_coefficients(f_triangle,   "triangle (paire)")
a0_i,  an_i,  bn_i  = afficher_coefficients(f_creneau,    "creneau (impaire)")
a0_q,  an_q,  bn_q  = afficher_coefficients(f_quelconque, "exp(x)")

# ============================================================
#  Graphique : barres des coefficients
# ============================================================
n_vals  = list(range(1, N_max + 1))
SEUIL   = 1e-6   # en dessous : barre non affichee

def tracer_barres(ax, n_vals, coeffs, prefixe, titre, couleur):
    """Trace les barres des coefficients et annote la valeur au pied de chaque barre."""
    valeurs_non_nulles = [v for v in coeffs if abs(v) >= SEUIL]
    ymax = max((abs(v) for v in valeurs_non_nulles), default=1)

    for n, v in zip(n_vals, coeffs):
        if abs(v) >= SEUIL:
            ax.bar(n, v, color=couleur, alpha=0.8, width=0.6)
        # Annotation toujours affichee
        label = f'{prefixe}{n}=0' if abs(v) < SEUIL else f'{prefixe}{n}={v:.2f}'
        y_txt = -ymax * 0.05 if v >= 0 else ymax * 0.05
        va    = 'top'         if v >= 0 else 'bottom'
        ax.text(n, y_txt, label,
                ha='center', va=va, fontsize=7, rotation=90)

    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_ylim(-ymax * 1.5, ymax * 1.5)
    ax.set_title(titre, fontsize=9)
    ax.set_xlabel('n', fontsize=8)
    ax.set_xticks(n_vals)
    ax.grid(True, alpha=0.3, axis='y')

x_plot = np.linspace(-T, T, 1000)

donnees = [
    (f_triangle,   an_p, bn_p, "Triangle (PAIRE)",          "teal"),
    (f_creneau,    an_i, bn_i, "Creneau (IMPAIRE)",          "crimson"),
    (f_quelconque, an_q, bn_q, "exp(x)",                     "purple"),
]

fig, axes = plt.subplots(3, 3, figsize=(14, 9))

for row, (f, an, bn, titre, couleur) in enumerate(donnees):
    # Colonne 0 : trace de la fonction
    axes[row, 0].plot(x_plot, f(x_plot), color=couleur, linewidth=2)
    axes[row, 0].axhline(0, color='black', linewidth=0.6)
    axes[row, 0].axvline(0, color='black', linewidth=0.6)
    axes[row, 0].set_title(f'{titre} -- f(x)', fontsize=9)
    axes[row, 0].grid(True, alpha=0.3)

    # Colonnes 1 et 2 : barres des coefficients
    tracer_barres(axes[row, 1], n_vals, an, 'a', f'{titre} -- $a_n$', couleur)
    tracer_barres(axes[row, 2], n_vals, bn, 'b', f'{titre} -- $b_n$', couleur)

fig.suptitle("Lien parite / coefficients de Fourier", fontsize=12)
plt.tight_layout()
plt.savefig('ex4_lien_fourier.png', dpi=150)
plt.show()
