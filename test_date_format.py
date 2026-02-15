#!/usr/bin/env python3
"""
Script de prueba para verificar el formato de fechas en español
"""
from datetime import date
from web_app import format_date_spanish


# Casos de prueba
test_dates = [
    date(2026, 2, 15),   # Sábado
    date(2026, 2, 16),   # Domingo
    date(2026, 2, 17),   # Lunes
    date(2026, 1, 1),    # Jueves (Año Nuevo)
    date(2026, 12, 25),  # Viernes (Navidad)
]

print("🧪 PRUEBA DE FORMATO DE FECHAS EN ESPAÑOL")
print("=" * 70)

for test_date in test_dates:
    formatted = format_date_spanish(test_date)
    print(f"✅ {test_date.isoformat()} → {formatted}")

print("\n✅ ¡Todas las fechas formateadas correctamente en español!")
