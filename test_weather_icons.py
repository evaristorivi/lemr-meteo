#!/usr/bin/env python3
"""
Script de prueba para verificar la función de selección de iconos meteorológicos
"""
from web_app import get_weather_icon_from_text


# Ejemplos de predicciones reales de AEMET
test_cases = [
    ("Cielos despejados durante todo el día.", "☀️"),
    ("Poco nuboso con intervalos de nubes altas.", "🌤️"),
    ("Intervalos nubosos aumentando a muy nuboso por la tarde.", "⛅"),
    ("Muy nuboso o cubierto con precipitaciones débiles.", "☁️"), 
    ("Chubascos dispersos, ocasionalmente con tormenta.", "🌧️"),
    ("Lluvia fuerte con posibilidad de tormenta.", "🌧️"),
    ("Tormentas localmente fuertes por la tarde.", "⛈️"),
    ("Nevadas débiles en cotas altas.", "🌨️"),
    ("Nieblas matinales en valles, disipándose al mediodía.", "🌫️"),
    ("Vientos fuertes del noroeste con rachas muy fuertes.", "💨"),
    ("Chubascos y tormentas ocasionales.", "🌦️"),
    ("Intervalos nubosos sin precipitaciones.", "⛅"),
    ("", "🌦️"),  # Texto vacío, debería dar el default
]


def run_tests():
    print("🧪 PRUEBA DE ICONOS METEOROLÓGICOS DINÁMICOS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, (text, expected) in enumerate(test_cases, 1):
        result = get_weather_icon_from_text(text)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        text_preview = text[:50] + "..." if len(text) > 50 else text
        print(f"{status} Test {i}: {result} (esperado: {expected})")
        print(f"   Texto: '{text_preview}'")
        
        if result != expected:
            print(f"   ⚠️  FALLÓ: Se obtuvo '{result}' pero se esperaba '{expected}'")
        print()
    
    print("=" * 70)
    print(f"📊 RESULTADO: {passed}/{len(test_cases)} tests pasados")
    if failed > 0:
        print(f"⚠️  {failed} tests fallaron")
    else:
        print("✅ ¡Todos los tests pasaron!")
    
    print("\n🎨 LEYENDA DE ICONOS:")
    icons = {
        "☀️": "Despejado / Soleado",
        "🌤️": "Poco nuboso",
        "⛅": "Parcialmente nuboso / Intervalos",
        "☁️": "Muy nuboso / Cubierto",
        "🌧️": "Lluvia / Chubascos",
        "🌦️": "Precipitación variable (default)",
        "⛈️": "Tormentas",
        "🌨️": "Nieve",
        "🌫️": "Niebla",
        "💨": "Viento fuerte",
    }
    
    for icon, desc in icons.items():
        print(f"   {icon}  {desc}")


if __name__ == "__main__":
    run_tests()
