#!/usr/bin/env python3
"""
Script para verificar los límites de rate limit de GitHub Models
"""
import config
from openai import OpenAI


def check_rate_limits():
    """Verifica los límites actuales de la API"""
    
    if not config.GITHUB_TOKEN:
        print("❌ No se ha configurado GITHUB_TOKEN")
        return
    
    print("🔍 Verificando límites de GitHub Models...\n")
    
    # Configurar cliente
    client = OpenAI(
        api_key=config.GITHUB_TOKEN,
        base_url="https://models.inference.ai.azure.com"
    )
    
    # Obtener lista de modelos de la cascada
    model_cascade = getattr(config, "AI_MODEL_CASCADE", [
        'gpt-4o',
        'gpt-4o-mini',
        'meta-llama-3.1-405b-instruct',
        'phi-4'
    ])
    
    print("📊 ESTADO DE LA CASCADA DE MODELOS")
    print("=" * 60)
    
    available_models = []
    exhausted_models = []
    
    for idx, model in enumerate(model_cascade, 1):
        try:
            print(f"\n{idx}. Probando: {model}")
            
            # Hacer una llamada mínima
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Hi"}
                ],
                max_tokens=1
            )
            
            # Extraer información de rate limits
            if hasattr(response, '_response') and hasattr(response._response, 'headers'):
                headers = response._response.headers
                
                limit = headers.get('x-ratelimit-limit-requests', 'N/A')
                remaining = headers.get('x-ratelimit-remaining-requests', 'N/A')
                reset = headers.get('x-ratelimit-reset-requests', 'N/A')
                
                print(f"   ├─ Límite total: {limit} requests/día")
                print(f"   ├─ Restantes: {remaining} requests")
                print(f"   └─ Reset: {reset}")
                
                # Calcular porcentaje usado
                if limit != 'N/A' and remaining != 'N/A':
                    try:
                        used = int(limit) - int(remaining)
                        pct = (used / int(limit)) * 100
                        remaining_int = int(remaining)
                        
                        if remaining_int > 0:
                            print(f"   ✅ DISPONIBLE: {remaining}/{limit} ({100-pct:.1f}% libre)")
                            available_models.append((model, remaining_int))
                        else:
                            print(f"   ❌ AGOTADO: 0/{limit}")
                            exhausted_models.append(model)
                    except:
                        print(f"   ✅ DISPONIBLE (sin info de límites)")
                        available_models.append((model, '?'))
            else:
                print(f"   ✅ DISPONIBLE (sin cabeceras de rate limit)")
                available_models.append((model, '?'))
            
        except Exception as e:
            error_msg = str(e)
            
            # Verificar si es un error de rate limit
            if "429" in error_msg or "rate limit" in error_msg.lower():
                print(f"   ❌ AGOTADO - Rate limit alcanzado")
                exhausted_models.append(model)
            else:
                print(f"   ⚠️  Error: {error_msg[:80]}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print("=" * 60)
    
    if available_models:
        print(f"\n✅ Modelos DISPONIBLES ({len(available_models)}):")
        for i, (model, remaining) in enumerate(available_models, 1):
            star = "⭐" if i == 1 else "  "
            print(f"   {star} {i}. {model} (restantes: {remaining})")
        print(f"\n🎯 El sistema usará automáticamente: {available_models[0][0]}")
    else:
        print("\n❌ NO HAY MODELOS DISPONIBLES")
    
    if exhausted_models:
        print(f"\n❌ Modelos AGOTADOS ({len(exhausted_models)}):")
        for i, model in enumerate(exhausted_models, 1):
            print(f"   {i}. {model}")
        print("\n⏰ Se resetearán en el próximo ciclo de 24h")


if __name__ == "__main__":
    check_rate_limits()
    
    print("\n" + "=" * 60)
    print("⚙️  CONFIGURACIÓN DEL SISTEMA DE CASCADA")
    print("=" * 60)
    print(f"\nProvider: {config.AI_PROVIDER}")
    
    cascade = getattr(config, "AI_MODEL_CASCADE", [])
    if cascade:
        print(f"\n🔄 Orden de la cascada automática:")
        for i, model in enumerate(cascade, 1):
            print(f"   {i}. {model}")
    
    print(f"\n💡 El sistema prueba automáticamente cada modelo en orden")
    print(f"   hasta encontrar uno disponible. ¡No necesitas hacer nada!")
    print(f"\n🔗 Más info: https://docs.github.com/en/github-models")
