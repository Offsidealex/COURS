import numpy as np
import matplotlib.pyplot as plt

# ============================================================
#  Exercice 3 -- Decomposition en partie paire + partie impaire
#
#  Toute fonction f peut s'ecrire : f = f_paire + f_impaire
#  avec :
#    f_paire(x)   = [f(x) + f(-x)] / 2
#    f_impaire(x) = [f(x) - f(-x)] / 2
# ============================================================

x = np.linspace(-2 * np.pi, 2 * np.pi, 1000)

def partie_paire(f, x):
    return (f(x) + f(-x)) / 2

def partie_impaire(f, x):
    return (f(x) - f(-x)) / 2

# --- Fonctions a decomposer ---
fonctions = [
    (lambda x: x**2 + x,  "x^2 + x"),
    (lambda x: np.exp(x), "exp(x)"),
]

fig, axes = plt.subplots(len(fonctions), 3, figsize=(14, 4 * len(fonctions)))

for i, (f, nom) in enumerate(fonctions):
    y    = f(x)
    y_p  = partie_paire(f, x)
    y_i  = partie_impaire(f, x)

    # Verification : y_p + y_i doit redonner f
    erreur = np.max(np.abs(y - (y_p + y_i)))
    print(f"f(x) = {nom}  =>  erreur reconstruction : {erreur:.2e}")

    # Colonne 1 : f originale
    axes[i, 0].plot(x, y, color='steelblue', linewidth=2)
    axes[i, 0].axhline(0, color='gray', linewidth=0.6)
    axes[i, 0].axvline(0, color='gray', linewidth=0.6)
    axes[i, 0].set_title(f'f(x) = {nom}', fontsize=10)
    axes[i, 0].grid(True, alpha=0.3)

    # Colonne 2 : partie paire
    axes[i, 1].plot(x, y_p, color='teal', linewidth=2)
    axes[i, 1].axhline(0, color='gray', linewidth=0.6)
    axes[i, 1].axvline(0, color='gray', linewidth=0.6)
    axes[i, 1].set_title(f'Partie paire de {nom}', fontsize=10)
    axes[i, 1].grid(True, alpha=0.3)

    # Colonne 3 : partie impaire
    axes[i, 2].plot(x, y_i, color='crimson', linewidth=2)
    axes[i, 2].axhline(0, color='gray', linewidth=0.6)
    axes[i, 2].axvline(0, color='gray', linewidth=0.6)
    axes[i, 2].set_title(f'Partie impaire de {nom}', fontsize=10)
    axes[i, 2].grid(True, alpha=0.3)

# En-tetes colonnes
for ax, titre in zip(axes[0], ["f(x) originale", "Partie PAIRE", "Partie IMPAIRE"]):
    ax.set_xlabel('')

fig.suptitle("Decomposition d'une fonction en partie paire + partie impaire", fontsize=13)
plt.tight_layout()
plt.savefig('ex3_decomposition.png', dpi=150)
plt.show()

# ============================================================
#  Verification visuelle de la symetrie des parties
# ============================================================
f_test = lambda x: np.exp(x)
nom_test = "exp(x)"

fig, ax = plt.subplots(figsize=(10, 5))
y_p = partie_paire(f_test, x)
y_i = partie_impaire(f_test, x)

ax.plot(x, f_test(x), 'k-',  linewidth=2.5, label=f'f(x) = {nom_test}')
ax.plot(x, y_p,       'b--', linewidth=2,   label='Partie paire  = cosh(x)')
ax.plot(x, y_i,       'r-.',  linewidth=2,   label='Partie impaire = sinh(x)')
ax.axhline(0, color='gray', linewidth=0.6)
ax.axvline(0, color='gray', linewidth=0.6)
ax.set_title(f"Decomposition de f(x) = {nom_test}", fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('ex3_exp_decompose.png', dpi=150)
plt.show()
