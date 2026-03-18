import numpy as np
import matplotlib.pyplot as plt

# ============================================================
#  Exercice 2 -- Verification numerique de la parite
#
#  Pour une fonction paire  : f(-x) - f(x) = 0 partout
#  Pour une fonction impaire: f(-x) + f(x) = 0 partout
# ============================================================

x = np.linspace(-2 * np.pi, 2 * np.pi, 1000)
# On exclut x=0 pour eviter les divisions eventuelles
x_pos = x[x > 0]

def verifier_parite(f, nom, x):
    """Affiche si la fonction est paire, impaire ou ni l'une ni l'autre."""
    diff_paire   = np.max(np.abs(f(x) - f(-x)))   # doit etre 0 si paire
    diff_impaire = np.max(np.abs(f(x) + f(-x)))   # doit etre 0 si impaire
    seuil = 1e-9

    print(f"\n--- f(x) = {nom} ---")
    print(f"  max|f(x) - f(-x)| = {diff_paire:.2e}  {'<-- PAIRE' if diff_paire < seuil else ''}")
    print(f"  max|f(x) + f(-x)| = {diff_impaire:.2e}  {'<-- IMPAIRE' if diff_impaire < seuil else ''}")
    if diff_paire < seuil:
        print("  => La fonction est PAIRE")
    elif diff_impaire < seuil:
        print("  => La fonction est IMPAIRE")
    else:
        print("  => La fonction n'est NI paire NI impaire")

# --- Liste des fonctions a tester ---
fonctions = [
    (lambda x: np.cos(x), "cos(x)"),
    (lambda x: np.sin(x), "sin(x)"),
    (lambda x: x**2,      "x^2"),
    (lambda x: x**3,      "x^3"),
    # -------------------------------------------------------
    # A COMPLETER : ajoutez ici les deux fonctions suivantes
    #   f(x) = x^2 * cos(x)
    #   f(x) = x * sin(x)
    # Exemple de syntaxe :
    #   (lambda x: ..., "nom de la fonction"),
    # -------------------------------------------------------
]

print("=" * 50)
print("  VERIFICATION NUMERIQUE DE LA PARITE")
print("=" * 50)
for f, nom in fonctions:
    verifier_parite(f, nom, x)

# ============================================================
#  Trace de f(x) vs f(-x) pour chaque fonction
# ============================================================
n = len(fonctions)
cols = min(n, 3)
rows = (n + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
axes = np.array(axes).flatten()

couleurs = ['steelblue','crimson','teal','darkorange','purple','olive','brown','navy']

for ax, (f, nom), couleur in zip(axes, fonctions, couleurs):
    y     = f(x)
    y_sym = f(-x)
    ax.plot(x, y,     color=couleur, linewidth=2,   label='f(x)')
    ax.plot(x, y_sym, 'k--',         linewidth=1.2, label='f(-x)', alpha=0.6)
    ax.axhline(0, color='gray', linewidth=0.6)
    ax.axvline(0, color='gray', linewidth=0.6)
    ax.set_title(f'f(x) = {nom}', fontsize=9)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

fig.suptitle("Comparaison f(x) et f(-x)", fontsize=13)
plt.tight_layout()
plt.savefig('ex2_verification.png', dpi=150)
plt.show()
