# swagger_client.ProductosClimatologicosApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**balance_hdrico_nacional__documento_**](ProductosClimatologicosApi.md#balance_hdrico_nacional__documento_) | **GET** /api/productos/climatologicos/balancehidrico/{anio}/{decena} | Balance hídrico nacional (documento).
[**capas_shape_de_estaciones_climatolgicas_**](ProductosClimatologicosApi.md#capas_shape_de_estaciones_climatolgicas_) | **GET** /api/productos/climatologicos/capasshape/{tipoestacion} | Capas SHAPE de estaciones climatológicas de AEMET.
[**resumen_mensual_climatolgico_nacional__documento_**](ProductosClimatologicosApi.md#resumen_mensual_climatolgico_nacional__documento_) | **GET** /api/productos/climatologicos/resumenclimatologico/nacional/{anio}/{mes} | Resumen mensual climatológico nacional (documento).


# **balance_hdrico_nacional__documento_**
> Model200 balance_hdrico_nacional__documento_(anio, decena)

Balance hídrico nacional (documento).

Se obtiene, para la decema y el año pasados por parámetro, el Boletín Hídrico Nacional que se elabora cada diez días. Se presenta información resumida de forma distribuida para todo el territorio nacional de diferentes variables, en las que se incluye informaciones de la precipitación y la evapotranspiración potencial acumuladas desde el 1 de septiembre.

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
api_instance = swagger_client.ProductosClimatologicosApi(swagger_client.ApiClient(configuration))
anio = 'anio_example' # str | Año (AAAA)
decena = 'decena_example' # str | Decena de 01 (primera decena) a 36 (última decena)

try:
    # Balance hídrico nacional (documento).
    api_response = api_instance.balance_hdrico_nacional__documento_(anio, decena)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ProductosClimatologicosApi->balance_hdrico_nacional__documento_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **anio** | **str**| Año (AAAA) | 
 **decena** | **str**| Decena de 01 (primera decena) a 36 (última decena) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **capas_shape_de_estaciones_climatolgicas_**
> Model200 capas_shape_de_estaciones_climatolgicas_(tipoestacion)

Capas SHAPE de estaciones climatológicas de AEMET.

Capas SHAPE de las distintas estaciones climatológicas de AEMET: automáticas, completas, pluviométricas y termométricas.

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
api_instance = swagger_client.ProductosClimatologicosApi(swagger_client.ApiClient(configuration))
tipoestacion = 'tipoestacion_example' # str |  | Código | Tipo de Estación | |----------|----------| | automaticas  | Estaciones Automáticas   | | completas  | Estaciones Completas   | | pluviometricas  | Estaciones Pluviométricas   | | termometricas  | Estaciones Termométricas   

try:
    # Capas SHAPE de estaciones climatológicas de AEMET.
    api_response = api_instance.capas_shape_de_estaciones_climatolgicas_(tipoestacion)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ProductosClimatologicosApi->capas_shape_de_estaciones_climatolgicas_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tipoestacion** | **str**|  | Código | Tipo de Estación | |----------|----------| | automaticas  | Estaciones Automáticas   | | completas  | Estaciones Completas   | | pluviometricas  | Estaciones Pluviométricas   | | termometricas  | Estaciones Termométricas    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **resumen_mensual_climatolgico_nacional__documento_**
> Model200 resumen_mensual_climatolgico_nacional__documento_(anio, mes)

Resumen mensual climatológico nacional (documento).

Resumen climatológico nacional, para el año y mes pasado por parámetro, sobre el estado del clima y la evolución de las principales variables climáticas, en especial temperatura y precipitación, a nivel mensual, estacional y anual.

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
api_instance = swagger_client.ProductosClimatologicosApi(swagger_client.ApiClient(configuration))
anio = 'anio_example' # str | Año (AAAA)
mes = 'mes_example' # str | Mes (mm)

try:
    # Resumen mensual climatológico nacional (documento).
    api_response = api_instance.resumen_mensual_climatolgico_nacional__documento_(anio, mes)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ProductosClimatologicosApi->resumen_mensual_climatolgico_nacional__documento_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **anio** | **str**| Año (AAAA) | 
 **mes** | **str**| Mes (mm) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

