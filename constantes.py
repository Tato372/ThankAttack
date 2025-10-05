#Tamaño y Escalas
ANCHO_VENTANA = 1220
ALTO_VENTANA = 780
ALTO_TANQUE = 16    
ANCHO_TANQUE = 16
ANCHO_BALA = 4
ALTO_BALA = 4
ESCALA_TANQUE_ALTO = 1.75
ESCALA_TANQUE_ANCHO = 1.75
ESCALA_ANCHO_BALA = 1.5
ESCALA_ALTO_BALA = 1.5
ESCALA_CORAZON = 1.75
TAMAÑO_REJILLA = 32
FILAS = 50
COLUMNAS = 50
ESCALA_POCION = 1.5
ESCALA_MONEDA = 1.25
LIMITE_PANTALLA = 50
MAPA_ANCHO = COLUMNAS * TAMAÑO_REJILLA
MAPA_ALTO = FILAS * TAMAÑO_REJILLA



#Colores
AMARILLO = (255, 255, 0)
COLOR_BG = (0, 0, 20)
ROJO = (255, 0, 0)
ROJO_OSCURO = (139, 0, 0)
ROJO_TRANSPARENTE = (255, 0, 0, 100)
AZUL = (0, 0, 255)
VERDE = (0, 255, 0)
VERDE_OSCURO = (0, 139, 0) 
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AZUL_CIELO_VIVO= (0, 204, 255)
GRIS = (128, 128, 128)

# Colores retro
COLOR_FONDO = (40, 40, 40)        # gris oscuro
COLOR_BORDE = (200, 200, 200)     # blanco para el borde
COLOR_BORDE_SEL = (0, 255, 0)     # verde para selección
COLOR_TEXTO = (255, 255, 255)     # blanco

#Otros
FPS = 60
VELOCIDAD = 4
DISPARO_COOLDOWN = 1000  # en milisegundos
VELOCIDAD_BALA = 5
TIPOS_TILES = 7
RANGO_VISION = 1000000
RANGO_DISPARO = 300
CONFIG_TANQUES = {
            1: {  # 1 jugador
                "Facil":      {1: 11, 2: 11, 3: 6, 4: 3},
                "Intermedio": {1: 6,  2: 6,  3: 8, 4: 6},
                "Dificil":    {1: 6,  2: 6,  3: 11,4: 11},
            },
            2: {  # 2 jugadores
                "Facil":      {1: 20, 2: 20, 3: 10, 4: 5},
                "Intermedio": {1: 10,  2: 10,  3: 15, 4: 10},
                "Dificil":    {1: 10,  2: 10,  3: 20, 4: 20},
                "Pesadilla":  {4: 40, 5: 10},  # solo tanques rojos y definitivos
            }
        }
# constantes.py
TANQUE_STATS = {
    1: {  # Verde - Tipo 1
        "velocidad": 1.0,          # Lento
        "vida": 20,
        "cooldown_disparo": 3000,  # Disparo lento (ms)
    },
    2: {  # Amarillo - Tipo 2
        "velocidad": 1.0,          # Lento
        "vida": 30,
        "cooldown_disparo": 1000,   # Disparo rápido
    },
    3: {  # Marrón - Tipo 3
        "velocidad": 2.0,          # Rápido
        "vida": 40,
        "cooldown_disparo": 1000,   # Disparo rápido
    },
    4: {  # Rojo - Tipo 4
        "velocidad": 1.0,          # Lento
        "vida": 50,
        "cooldown_disparo": 3000,  # Disparo lento
    },
    5: {  # Negro - Definitivo
        "velocidad": 1.0,          # Lento
        "vida": 100,
        "cooldown_disparo": 1000,   # Disparo rápido
    }
}

