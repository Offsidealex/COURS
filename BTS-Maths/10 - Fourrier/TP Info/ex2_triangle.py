import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad

# ============================================================
#  Parametres globaux
# ============================================================
T = 2 * np.pi
N_points = 1000
x = np.linspace(-2 * np.pi, 2 * np.pi, N_points)
N_max = 10

# Graduations en multiples de pi
pi_ticks  = np.arange(-2, 3) * np.pi
pi_labels = [r'$-2\pi$', r'$-\pi$', r'$0$', r'$\pi$', r'$2\pi$']
y_ticks   = [-np.pi/2, 0, np.pi/2]
y_labels  = [r'$-\frac{\pi}{2}$', r'$0$', r'$\frac{\pi}{2}$']

def set_axes_ticks(ax):
    ax.set_xticks(pi_ticks)
    ax.set_xticklabels(pi_labels)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontweight='bold')

# ============================================================
#  Fonctions de calcul (identiques a ex1)
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

# ============================================================
#  Definition de la fonction triangle
# ============================================================
def f_triangle(x):
    x_mod = x % T
    return np.abs(x_mod - np.pi) - np.pi / 2

# ============================================================
#  1) Calcul et affichage des coefficients
# ============================================================
a0_tri = calcul_a0(f_triangle, T)
a_tri  = [calcul_an(f_triangle, T, n) for n in range(1, N_max + 1)]
b_tri  = [calcul_bn(f_triangle, T, n) for n in range(1, N_max + 1)]

print(f"a0 = {a0_tri:.6f}")
print("\n  n  |    a_n    |    b_n")
print("-----|-----------|----------")
for n in range(1, N_max + 1):
    print(f"  {n:2d} | {a_tri[n-1]:+.6f} | {b_tri[n-1]:+.6f}")

# ============================================================
#  2) Trace : fonction originale + approximations
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, N in zip(axes, [1, 3, 50]):
    SN = approximation_partielle(x, f_triangle, T, N)
    ax.plot(x, f_triangle(x), 'k--', linewidth=1.5, alpha=0.6, label='f(x)')
    ax.plot(x, SN, color='teal', linewidth=1.5, label=f'S_{N}(x)')
    ax.set_title(f'Ordre N = {N}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    set_axes_ticks(ax)

fig.suptitle("Serie de Fourier -- Fonction triangle", fontsize=13)
plt.tight_layout()
plt.savefig('approximations_triangle.png', dpi=150)
plt.show()
