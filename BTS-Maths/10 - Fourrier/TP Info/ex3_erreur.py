import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad

# ============================================================
#  Parametres globaux
# ============================================================
T = 2 * np.pi
N_points = 1000
x = np.linspace(0, 2 * T, N_points)

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

def f_creneau(x):
    x_mod = x % T
    return np.where(x_mod < np.pi, 1.0, -1.0)

def f_triangle(x):
    x_mod = x % T
    return np.abs(x_mod - np.pi) - np.pi / 2

# ============================================================
#  Calcul de l'erreur quadratique
# ============================================================
def erreur_quadratique(f, T, N, N_pts=2000):
    x_eval = np.linspace(0, T, N_pts)
    SN = approximation_partielle(x_eval, f, T, N)
    return np.sqrt(np.mean((f(x_eval) - SN) ** 2))

# ============================================================
#  Calcul pour N = 1 a 20
# ============================================================
ordres_test = list(range(1, 21))

print("Calcul en cours, patientez...")
erreurs_creneau  = [erreur_quadratique(f_creneau,  T, N) for N in ordres_test]
erreurs_triangle = [erreur_quadratique(f_triangle, T, N) for N in ordres_test]

# ============================================================
#  Trace des courbes de convergence
# ============================================================
plt.figure(figsize=(9, 5))
plt.semilogy(ordres_test, erreurs_creneau,  'o-', color='crimson', label='Creneau')
plt.semilogy(ordres_test, erreurs_triangle, 's-', color='teal',    label='Triangle')
plt.xlabel("Ordre N")
plt.ylabel("Erreur quadratique (echelle log)")
plt.title("Convergence de la serie de Fourier")
plt.legend()
plt.grid(True, which='both', alpha=0.3)
plt.tight_layout()
plt.savefig('erreur_convergence.png', dpi=150)
plt.show()

# ============================================================
#  Affichage du tableau des erreurs
# ============================================================
print(f"\n{'N':>4} | {'Erreur creneau':>16} | {'Erreur triangle':>16}")
print("-" * 44)
for N, ec, et in zip(ordres_test, erreurs_creneau, erreurs_triangle):
    print(f"{N:>4} | {ec:>16.8f} | {et:>16.8f}")
