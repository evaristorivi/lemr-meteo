# swagger_client.RedesEspecialesApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**contenido_total_de_ozono__tiempo_actual_**](RedesEspecialesApi.md#contenido_total_de_ozono__tiempo_actual_) | **GET** /api/red/especial/ozono | Contenido total de ozono. Tiempo actual.
[**datos_de_contaminacin_de_fondo__tiempo_actual_**](RedesEspecialesApi.md#datos_de_contaminacin_de_fondo__tiempo_actual_) | **GET** /api/red/especial/contaminacionfondo/estacion/{nombre_estacion} | Datos de contaminación de fondo. Tiempo actual.
[**datos_de_radiacin_global_directa_o_difusa__tiempo_actual_**](RedesEspecialesApi.md#datos_de_radiacin_global_directa_o_difusa__tiempo_actual_) | **GET** /api/red/especial/radiacion | Datos de radiación global, directa o difusa. Tiempo actual.
[**perfiles_verticales_de_ozono__tiempo_actual_**](RedesEspecialesApi.md#perfiles_verticales_de_ozono__tiempo_actual_) | **GET** /api/red/especial/perfilozono/estacion/{estacion} | Perfiles verticales de ozono. Tiempo actual.


# **contenido_total_de_ozono__tiempo_actual_**
> Model200 contenido_total_de_ozono__tiempo_actual_()

Contenido total de ozono. Tiempo actual.

Dato medio diario de contenido total de ozono. Cada 24 h (actualmente, en fines de semana, festivos y vacaciones no se genera por la falta de personal en el Centro Radiométrico Nacional).

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: api_key
configuration = swagger_client.Configuration()
configuration.api_key['api_key'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['api_key'] = 'Bearer'

# create an instance of the API class
api_instance = swagger_client.RedesEspecialesApi(swagger_client.ApiClient(configuration))

try:
    # Contenido total de ozono. Tiempo actual.
    api_response = api_instance.contenido_total_de_ozono__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling RedesEspecialesApi->contenido_total_de_ozono__tiempo_actual_: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **datos_de_contaminacin_de_fondo__tiempo_actual_**
> Model200 datos_de_contaminacin_de_fondo__tiempo_actual_(nombre_estacion)

Datos de contaminación de fondo. Tiempo actual.

Ficheros diarios con datos diezminutales de la estación de la red de contaminación de fondo EMEP/VAG/CAMP pasada por parámetro, de temperatura, presión, humedad, viento (dirección y velocidad), radiación global, precipitación y 4 componentes químicos: O3,SO2,NO,NO2 y PM10. Los datos se encuentran en formato FINN (propio del Ministerio de Medio Ambiente). Periodicidad: cada hora.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: api_key
configuration = swagger_client.Configuration()
configuration.api_key['api_key'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['api_key'] = 'Bearer'

# create an instance of the API class
api_instance = swagger_client.RedesEspecialesApi(swagger_client.ApiClient(configuration))
nombre_estacion = 'nombre_estacion_example' # str |  | Código | Estación de la Red EMEP | |----------|----------| | 11  | Barcarrota (Badajoz)   | | 10  | Cabo de Creus (Girona)   | | 09  | Campisábalos (Guadalajara)   | | 17  | Doñana (Huelva)  | | 14  | Els Torms (Lleida)   | | 06  | Mahón (Illes Balears)   | | 08  | Niembro-Llanes (Asturias)   | | 05  | Noia (A Coruña)   | | 16  | O Saviñao (Lugo)   | | 13  | Peñausende (Zamora)   | | 01  | San Pablo de los Montes (Toledo)   | | 07  | Víznar (Granada)   | | 12  | Zarra (Valencia) 

try:
    # Datos de contaminación de fondo. Tiempo actual.
    api_response = api_instance.datos_de_contaminacin_de_fondo__tiempo_actual_(nombre_estacion)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling RedesEspecialesApi->datos_de_contaminacin_de_fondo__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **nombre_estacion** | **str**|  | Código | Estación de la Red EMEP | |----------|----------| | 11  | Barcarrota (Badajoz)   | | 10  | Cabo de Creus (Girona)   | | 09  | Campisábalos (Guadalajara)   | | 17  | Doñana (Huelva)  | | 14  | Els Torms (Lleida)   | | 06  | Mahón (Illes Balears)   | | 08  | Niembro-Llanes (Asturias)   | | 05  | Noia (A Coruña)   | | 16  | O Saviñao (Lugo)   | | 13  | Peñausende (Zamora)   | | 01  | San Pablo de los Montes (Toledo)   | | 07  | Víznar (Granada)   | | 12  | Zarra (Valencia)  | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **datos_de_radiacin_global_directa_o_difusa__tiempo_actual_**
> Model200 datos_de_radiacin_global_directa_o_difusa__tiempo_actual_()

Datos de radiación global, directa o difusa. Tiempo actual.

Datos horarios (HORA SOLAR VERDADERA) acumulados de radiación  global, directa, difusa e infrarroja, y datos semihorarios  (HORA SOLAR VERDADERA) acumulados de radiación ultravioleta eritemática.Datos diarios acumulados  de radiación global, directa, difusa, ultravioleta eritemática e infrarroja. Periodicidad: Cada 24h (actualmente en fines de semana, festivos y vacaciones, no se genera por la ausencia de personal en el Centro Radiométrico Nacional).

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: api_key
configuration = swagger_client.Configuration()
configuration.api_key['api_key'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['api_key'] = 'Bearer'

# create an instance of the API class
api_instance = swagger_client.RedesEspecialesApi(swagger_client.ApiClient(configuration))

try:
    # Datos de radiación global, directa o difusa. Tiempo actual.
    api_response = api_instance.datos_de_radiacin_global_directa_o_difusa__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling RedesEspecialesApi->datos_de_radiacin_global_directa_o_difusa__tiempo_actual_: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **perfiles_verticales_de_ozono__tiempo_actual_**
> Model200 perfiles_verticales_de_ozono__tiempo_actual_(estacion)

Perfiles verticales de ozono. Tiempo actual.

Perfil Vertical de Ozono de la estación pasada por parámetro. Periodicidad: cada 7 días.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: api_key
configuration = swagger_client.Configuration()
configuration.api_key['api_key'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['api_key'] = 'Bearer'

# create an instance of the API class
api_instance = swagger_client.RedesEspecialesApi(swagger_client.ApiClient(configuration))
estacion = 'estacion_example' # str |  | Código | Estación | |----------|----------| | canarias  | Izaña   | | peninsula  | Madrid   

try:
    # Perfiles verticales de ozono. Tiempo actual.
    api_response = api_instance.perfiles_verticales_de_ozono__tiempo_actual_(estacion)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling RedesEspecialesApi->perfiles_verticales_de_ozono__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **estacion** | **str**|  | Código | Estación | |----------|----------| | canarias  | Izaña   | | peninsula  | Madrid    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

