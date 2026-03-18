import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad

# ============================================================
#  Parametres globaux
# ============================================================
T = 2 * np.pi        # Periode
N_points = 1000      # Nombre de points pour le trace
x = np.linspace(-2 * np.pi, 2 * np.pi, N_points)

# Graduations en multiples de pi
pi_ticks = np.arange(-2, 3) * np.pi
pi_labels = [r'$-2\pi$', r'$-\pi$', r'$0$', r'$\pi$', r'$2\pi$']

y_ticks = [-1, 0, 1]
y_labels = [r'$-1$', r'$0$', r'$1$']

def set_pi_ticks(ax):
    ax.set_xticks(pi_ticks)
    ax.set_xticklabels(pi_labels)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontweight='bold')

# ============================================================
#  Definition de la fonction creneau
# ============================================================
def f_creneau(x):
    x_mod = x % T
    return np.where(x_mod < np.pi, 1.0, -1.0)

# ============================================================
#  Fonctions de calcul des coefficients de Fourier
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
        an = calcul_an(f, T, n)
        bn = calcul_bn(f, T, n)
        S += an * np.cos(2 * np.pi * n * x / T)
        S += bn * np.sin(2 * np.pi * n * x / T)
    return S

# ============================================================
#  1) Trace de la fonction creneau
# ============================================================
fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(x, f_creneau(x), color='steelblue', linewidth=2, label='f(x) creneau')
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xlabel('x')
ax.set_ylabel('f(x)')
ax.set_title('Fonction creneau')
ax.legend()
ax.grid(True, alpha=0.3)
set_pi_ticks(ax)
plt.tight_layout()
plt.savefig('creneau_original.png', dpi=150)
plt.show()

# ============================================================
#  2) Calcul et affichage des coefficients a0, an, bn
# ============================================================
N_max = 10

a0 = calcul_a0(f_creneau, T)
a_coeffs = [calcul_an(f_creneau, T, n) for n in range(1, N_max + 1)]
b_coeffs = [calcul_bn(f_creneau, T, n) for n in range(1, N_max + 1)]

print(f"a0 = {a0:.6f}")
print("\n  n  |    a_n    |    b_n")
print("-----|-----------|----------")
for n in range(1, N_max + 1):
    print(f"  {n:2d} | {a_coeffs[n-1]:+.6f} | {b_coeffs[n-1]:+.6f}")

# ============================================================
#  3) Approximations partielles pour plusieurs ordres N
# ============================================================
ordres = [1, 3, 5, 15, 100]
fig, axes = plt.subplots(len(ordres), 1, figsize=(10, 3 * len(ordres)), sharex=True)

for ax, N in zip(axes, ordres):
    SN = approximation_partielle(x, f_creneau, T, N)
    ax.plot(x, f_creneau(x), 'k--', linewidth=1, alpha=0.5, label='f(x)')
    ax.plot(x, SN, color='crimson', linewidth=1.5, label=f'S_{N}(x)')
    ax.set_ylabel('Amplitude')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-1.5, 1.5)
    set_pi_ticks(ax)

axes[-1].set_xlabel('x')
fig.suptitle("Approximations partielles de la fonction creneau", fontsize=13)
plt.tight_layout()
plt.savefig('approximations_creneau.png', dpi=150)
plt.show()
