# swagger_client.RedRadaresApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**imagen_composicin_nacional_radares__tiempo_actual_estndar_**](RedRadaresApi.md#imagen_composicin_nacional_radares__tiempo_actual_estndar_) | **GET** /api/red/radar/nacional | Imagen composición nacional radares. Tiempo actual estándar.
[**radar_regional**](RedRadaresApi.md#radar_regional) | **GET** /api/red/radar/regional/{radar} | Imagen gráfica radar regional. Tiempo actual estándar.


# **imagen_composicin_nacional_radares__tiempo_actual_estndar_**
> Model200 imagen_composicin_nacional_radares__tiempo_actual_estndar_()

Imagen composición nacional radares. Tiempo actual estándar.

Imagen composición nacional radares. Tiempo actual estándar. Periodicidad: 30 minutos.

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
api_instance = swagger_client.RedRadaresApi(swagger_client.ApiClient(configuration))

try:
    # Imagen composición nacional radares. Tiempo actual estándar.
    api_response = api_instance.imagen_composicin_nacional_radares__tiempo_actual_estndar_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling RedRadaresApi->imagen_composicin_nacional_radares__tiempo_actual_estndar_: %s\n" % e)
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

# **radar_regional**
> Model200 radar_regional(radar)

Imagen gráfica radar regional. Tiempo actual estándar.

Imagen del radar regional de la región pasada por parámetro. Tiempo actual estándar. Periodicidad: 10 minutos.

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
api_instance = swagger_client.RedRadaresApi(swagger_client.ApiClient(configuration))
radar = 'radar_example' # str |  | Código | Radar | |----------|----------| | am  | Almería   | | sa  | Asturias   | | pm  | Illes Balears   | | ba  | Barcelona  | | cc  | Cáceres   | | co  | A Coruña   | | ma  | Madrid   | | ml  | Málaga   | | mu  | Murcia   | | vd  | Palencia   | | ca  | Las Palmas   | | se  | Sevilla   | | va  | Valencia   | | ss  | Vizcaya   | | za  | Zaragoza   

try:
    # Imagen gráfica radar regional. Tiempo actual estándar.
    api_response = api_instance.radar_regional(radar)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling RedRadaresApi->radar_regional: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **radar** | **str**|  | Código | Radar | |----------|----------| | am  | Almería   | | sa  | Asturias   | | pm  | Illes Balears   | | ba  | Barcelona  | | cc  | Cáceres   | | co  | A Coruña   | | ma  | Madrid   | | ml  | Málaga   | | mu  | Murcia   | | vd  | Palencia   | | ca  | Las Palmas   | | se  | Sevilla   | | va  | Valencia   | | ss  | Vizcaya   | | za  | Zaragoza    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

