import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad

# ============================================================
#  Parametres globaux
# ============================================================
T = 2 * np.pi
N_points = 1000
x = np.linspace(0, 2 * T, N_points)
N_max = 10

# ============================================================
#  Fonctions de calcul
# ============================================================
def calcul_a0(f, T):
    integrale, _ = quad(f, 0, T)
    return (2 / T) * integrale

def calcul_an(f, T, n):
    integrande = lambda x: f(x) * np.cos(2 * np.pi * n * x / T)
    integrale, _ = quad(integrande, 0, T)
    return (2 / T) * integrale

def calcul_bn(f, T, n):
    integrande = lambda x: f(x) * np.sin(2 * np.pi * n * x / T)
    integrale, _ = quad(integrande, 0, T)
    return (2 / T) * integrale

def approximation_partielle(x, f, T, N):
    a0 = calcul_a0(f, T)
    S = np.full_like(x, a0 / 2, dtype=float)
    for n in range(1, N + 1):
        S += calcul_an(f, T, n) * np.cos(2 * np.pi * n * x / T)
        S += calcul_bn(f, T, n) * np.sin(2 * np.pi * n * x / T)
    return S

def erreur_quadratique(f, T, N, N_pts=2000):
    x_eval = np.linspace(0, T, N_pts)
    SN = approximation_partielle(x_eval, f, T, N)
    return np.sqrt(np.mean((f(x_eval) - SN) ** 2))

# ============================================================
#  EXERCICE 4 : choisir UNE des trois fonctions ci-dessous
#
#  Decommenter le bloc correspondant a votre choix (et laisser
#  les deux autres commentes).
#
#  Choix possibles :
#    a) Dent de scie  : f(x) = x/T - 0.5         pour x dans [0, T[
#    b) Gaussienne    : f(x) = exp(-cos(x))       (definie sur R, T-periodique)
#    c) Parabolique   : f(x) = (x - pi)^2 - pi^2/3  pour x dans [0, T[
# ============================================================

def f_libre(x):

    # ------------------------------------------------------------------
    # CHOIX a) : Dent de scie
    #   f est lineaire par morceaux, impaire centree, a0 = 0
    #   Coefficients : bn = -1/(n*pi)  pour n >= 1,  tous an = 0
    # ------------------------------------------------------------------
    x_mod = x % T
    return x_mod / T - 0.5

    # ------------------------------------------------------------------
    # CHOIX b) : Gaussienne periodique
    #   f(x) = exp(-cos(x))
    #   Fonction paire => tous les bn sont nuls
    #   Les coefficients an font intervenir les fonctions de Bessel
    # ------------------------------------------------------------------
    #return np.exp(-np.cos(x))

    # ------------------------------------------------------------------
    # CHOIX c) : Parabolique (centree pour avoir a0 = 0)
    #   f(x) = (x - pi)^2 - pi^2/3   pour x dans [0, 2*pi[, puis repetee
    #   Fonction paire apres recentrage => tous les bn sont nuls
    #   Coefficients : an = 2/n^2  pour n >= 1
    # ------------------------------------------------------------------
    # x_mod = x % T
    #return (x_mod - np.pi) ** 2 - (np.pi ** 2) / 3

# ============================================================
#  1) Trace de la fonction
# ============================================================
plt.figure(figsize=(10, 3))
plt.plot(x, f_libre(x), color='purple', linewidth=2, label='f(x)')
plt.axhline(0, color='black', linewidth=0.8)
plt.xlabel('x')
plt.ylabel('f(x)')
plt.title('Fonction au choix')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('ex4_fonction.png', dpi=150)
plt.show()

# ============================================================
#  2) Calcul et affichage des coefficients
# ============================================================
a0 = calcul_a0(f_libre, T)
a_coeffs = [calcul_an(f_libre, T, n) for n in range(1, N_max + 1)]
b_coeffs = [calcul_bn(f_libre, T, n) for n in range(1, N_max + 1)]

print(f"a0 = {a0:.6f}")
print("\n  n  |    a_n    |    b_n")
print("-----|-----------|----------")
for n in range(1, N_max + 1):
    print(f"  {n:2d} | {a_coeffs[n-1]:+.6f} | {b_coeffs[n-1]:+.6f}")

# ============================================================
#  3) Approximations partielles
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, N in zip(axes, [1, 5, 20]):
    SN = approximation_partielle(x, f_libre, T, N)
    ax.plot(x, f_libre(x), 'k--', linewidth=1.5, alpha=0.6, label='f(x)')
    ax.plot(x, SN, color='purple', linewidth=1.5, label=f'S_{N}(x)')
    ax.set_title(f'Ordre N = {N}')
    ax.legend()
    ax.grid(True, alpha=0.3)

fig.suptitle("Serie de Fourier -- Fonction au choix", fontsize=13)
plt.tight_layout()
plt.savefig('ex4_approximations.png', dpi=150)
plt.show()

# ============================================================
#  4) Courbe de convergence de l'erreur
# ============================================================
ordres_test = list(range(1, 21))
print("Calcul de l'erreur, patientez...")
erreurs = [erreur_quadratique(f_libre, T, N) for N in ordres_test]

plt.figure(figsize=(8, 4))
plt.semilogy(ordres_test, erreurs, 'o-', color='purple')
plt.xlabel("Ordre N")
plt.ylabel("Erreur quadratique (echelle log)")
plt.title("Convergence -- Fonction au choix")
plt.grid(True, which='both', alpha=0.3)
plt.tight_layout()
plt.savefig('ex4_erreur.png', dpi=150)
plt.show()
