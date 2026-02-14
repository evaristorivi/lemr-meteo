# swagger_client.MaestroApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_municipio_using_get**](MaestroApi.md#get_municipio_using_get) | **GET** /api/maestro/municipio/{municipio} | getMunicipio
[**get_municipios_using_get**](MaestroApi.md#get_municipios_using_get) | **GET** /api/maestro/municipios | getMunicipios


# **get_municipio_using_get**
> Model200 get_municipio_using_get(municipio)

getMunicipio

Retorna información específica del municipio de España que se le pasa como parámetro.

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
api_instance = swagger_client.MaestroApi(swagger_client.ApiClient(configuration))
municipio = 'municipio_example' # str | Municipio

try:
    # getMunicipio
    api_response = api_instance.get_municipio_using_get(municipio)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MaestroApi->get_municipio_using_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **municipio** | **str**| Municipio | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_municipios_using_get**
> Model200 get_municipios_using_get()

getMunicipios

Retorna todos los municipios de España. Este servicio es útil para obtener información para utilizar otros elementos de AEMET OpenData, como por ejemplo, la predicción de municipios para 7 días o por  horas ya que nos retorna el id del municipio que necesitamos.

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
api_instance = swagger_client.MaestroApi(swagger_client.ApiClient(configuration))

try:
    # getMunicipios
    api_response = api_instance.get_municipios_using_get()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MaestroApi->get_municipios_using_get: %s\n" % e)
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

