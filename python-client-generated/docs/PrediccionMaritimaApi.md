# swagger_client.PrediccionMaritimaApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**prediccin_martima_costera_**](PrediccionMaritimaApi.md#prediccin_martima_costera_) | **GET** /api/prediccion/maritima/costera/costa/{costa} | Predicción marítima costera.
[**prediccin_martima_de_alta_mar_**](PrediccionMaritimaApi.md#prediccin_martima_de_alta_mar_) | **GET** /api/prediccion/maritima/altamar/area/{area} | Predicción marítima de alta mar.


# **prediccin_martima_costera_**
> Model200 prediccin_martima_costera_(costa)

Predicción marítima costera.

Predicción para un periodo de 24 horas de las condiciones meteorológicas para la zona costera pasada por parámetro.

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
api_instance = swagger_client.PrediccionMaritimaApi(swagger_client.ApiClient(configuration))
costa = 'costa_example' # str |  | Código | Área Costera | |----------|----------| | 42 | Costa de Andalucía Occidental y Ceuta   | | 47  | Costa de Andalucía Oriental y Melilla   | | 41  | Costa de Asturias, Cantabria y País Vasco  | | 45  | Costa de Cataluña   | | 40  | Costa de Galicia   | | 44  | Costa de Illes Balears   | | 43  | Costa de las Islas Canarias  | | 46  | Costa de Valencia y Murcia

try:
    # Predicción marítima costera.
    api_response = api_instance.prediccin_martima_costera_(costa)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionMaritimaApi->prediccin_martima_costera_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **costa** | **str**|  | Código | Área Costera | |----------|----------| | 42 | Costa de Andalucía Occidental y Ceuta   | | 47  | Costa de Andalucía Oriental y Melilla   | | 41  | Costa de Asturias, Cantabria y País Vasco  | | 45  | Costa de Cataluña   | | 40  | Costa de Galicia   | | 44  | Costa de Illes Balears   | | 43  | Costa de las Islas Canarias  | | 46  | Costa de Valencia y Murcia | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_martima_de_alta_mar_**
> Model200 prediccin_martima_de_alta_mar_(area)

Predicción marítima de alta mar.

Predicción para un periodo de 24 horas de las condiciones meteorológicas para el área marítima pasada por parámetro.

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
api_instance = swagger_client.PrediccionMaritimaApi(swagger_client.ApiClient(configuration))
area = 'area_example' # str |  | Código | Área de Alta Mar | |----------|----------| | 0 | Océano Atlántico al sur de 35º N   | | 1  | Océano Atlántico al norte de 30º N   | | 2  | Mar Mediterráneo

try:
    # Predicción marítima de alta mar.
    api_response = api_instance.prediccin_martima_de_alta_mar_(area)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionMaritimaApi->prediccin_martima_de_alta_mar_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **area** | **str**|  | Código | Área de Alta Mar | |----------|----------| | 0 | Océano Atlántico al sur de 35º N   | | 1  | Océano Atlántico al norte de 30º N   | | 2  | Mar Mediterráneo | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

