# swagger_client.IndicesIncendiosApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**mapa_de_niveles_de_riesgo_estimado_meteorolgico_de_incendios_forestales_**](IndicesIncendiosApi.md#mapa_de_niveles_de_riesgo_estimado_meteorolgico_de_incendios_forestales_) | **GET** /api/incendios/mapasriesgo/estimado/area/{area} | Mapa de niveles de riesgo estimado meteorológico de incendios forestales.
[**mapa_de_niveles_de_riesgo_previsto_meteorolgico_de_incendios_forestales_**](IndicesIncendiosApi.md#mapa_de_niveles_de_riesgo_previsto_meteorolgico_de_incendios_forestales_) | **GET** /api/incendios/mapasriesgo/previsto/dia/{dia}/area/{area} | Mapa de niveles de riesgo previsto meteorológico de incendios forestales.


# **mapa_de_niveles_de_riesgo_estimado_meteorolgico_de_incendios_forestales_**
> Model200 mapa_de_niveles_de_riesgo_estimado_meteorolgico_de_incendios_forestales_(area)

Mapa de niveles de riesgo estimado meteorológico de incendios forestales.

Último mapa elaborado de niveles de riesgo estimado meteorológico de incendios forestales para el área pasada por parámetro.

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
api_instance = swagger_client.IndicesIncendiosApi(swagger_client.ApiClient(configuration))
area = 'area_example' # str |  | Código | Área | |----------|----------| | p  | Península   | | b  | Baleares   | | c  | Canarias   

try:
    # Mapa de niveles de riesgo estimado meteorológico de incendios forestales.
    api_response = api_instance.mapa_de_niveles_de_riesgo_estimado_meteorolgico_de_incendios_forestales_(area)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling IndicesIncendiosApi->mapa_de_niveles_de_riesgo_estimado_meteorolgico_de_incendios_forestales_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **area** | **str**|  | Código | Área | |----------|----------| | p  | Península   | | b  | Baleares   | | c  | Canarias    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **mapa_de_niveles_de_riesgo_previsto_meteorolgico_de_incendios_forestales_**
> Model200 mapa_de_niveles_de_riesgo_previsto_meteorolgico_de_incendios_forestales_(dia, area)

Mapa de niveles de riesgo previsto meteorológico de incendios forestales.

Mapa elaborado de niveles de riesgo estimado meteorológico de incendios forestales para el día y el área pasados por parámetro.

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
api_instance = swagger_client.IndicesIncendiosApi(swagger_client.ApiClient(configuration))
dia = 'dia_example' # str |  | Código | Día | |----------|----------| | 1  | Mañana   | | 2  | Pasado Mañana   | | 3  | Dentro de 3 días   
area = 'area_example' # str |  | Código | Área | |----------|----------| | p  | Península   | | b  | Baleares   | | c  | Canarias   

try:
    # Mapa de niveles de riesgo previsto meteorológico de incendios forestales.
    api_response = api_instance.mapa_de_niveles_de_riesgo_previsto_meteorolgico_de_incendios_forestales_(dia, area)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling IndicesIncendiosApi->mapa_de_niveles_de_riesgo_previsto_meteorolgico_de_incendios_forestales_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dia** | **str**|  | Código | Día | |----------|----------| | 1  | Mañana   | | 2  | Pasado Mañana   | | 3  | Dentro de 3 días    | 
 **area** | **str**|  | Código | Área | |----------|----------| | p  | Península   | | b  | Baleares   | | c  | Canarias    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

