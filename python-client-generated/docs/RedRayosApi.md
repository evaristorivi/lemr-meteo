# swagger_client.RedRayosApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**mapa_con_los_rayos_registrados_en_periodo_standard__ltimo_elaborado_**](RedRayosApi.md#mapa_con_los_rayos_registrados_en_periodo_standard__ltimo_elaborado_) | **GET** /api/red/rayos/mapa | Mapa con los rayos registrados en periodo standard. Último elaborado.


# **mapa_con_los_rayos_registrados_en_periodo_standard__ltimo_elaborado_**
> Model200 mapa_con_los_rayos_registrados_en_periodo_standard__ltimo_elaborado_()

Mapa con los rayos registrados en periodo standard. Último elaborado.

Imagen de las descargas caídas en el territorio nacional durante un período de 12 horas.

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
api_instance = swagger_client.RedRayosApi(swagger_client.ApiClient(configuration))

try:
    # Mapa con los rayos registrados en periodo standard. Último elaborado.
    api_response = api_instance.mapa_con_los_rayos_registrados_en_periodo_standard__ltimo_elaborado_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling RedRayosApi->mapa_con_los_rayos_registrados_en_periodo_standard__ltimo_elaborado_: %s\n" % e)
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

