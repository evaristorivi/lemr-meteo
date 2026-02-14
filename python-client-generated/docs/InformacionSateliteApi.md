# swagger_client.InformacionSateliteApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ndice_normalizado_de_vegetacin_**](InformacionSateliteApi.md#ndice_normalizado_de_vegetacin_) | **GET** /api/satelites/producto/nvdi | Índice normalizado de vegetación.
[**temperatura_del_agua_del_mar_**](InformacionSateliteApi.md#temperatura_del_agua_del_mar_) | **GET** /api/satelites/producto/sst | Temperatura del agua del mar.


# **ndice_normalizado_de_vegetacin_**
> Model200 ndice_normalizado_de_vegetacin_()

Índice normalizado de vegetación.

Esta imagen se realiza con una combinación de los datos del canal visible y del infrarrojo cercano del satélite NOAA-19, que nos da una idea del desarrollo de la vegetación. Esto es así debido a que la vegetación absorbe fuertemente la radiación del canal visible, pero refleja fuertemente la del infrarrojo cercano. Esta imagen se renueva los jueves a última hora y contiene los datos acumulados de la última semana.

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
api_instance = swagger_client.InformacionSateliteApi(swagger_client.ApiClient(configuration))

try:
    # Índice normalizado de vegetación.
    api_response = api_instance.ndice_normalizado_de_vegetacin_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling InformacionSateliteApi->ndice_normalizado_de_vegetacin_: %s\n" % e)
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

# **temperatura_del_agua_del_mar_**
> Model200 temperatura_del_agua_del_mar_()

Temperatura del agua del mar.

Imagen obtenida con una combinación de los datos de los canales infrarrojos del satélite NOAA-19, que nos da la temperatura de la superficie del mar. Esta imagen se renueva todos los días a última hora y contiene los datos acumulados de los últimos siete días.

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
api_instance = swagger_client.InformacionSateliteApi(swagger_client.ApiClient(configuration))

try:
    # Temperatura del agua del mar.
    api_response = api_instance.temperatura_del_agua_del_mar_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling InformacionSateliteApi->temperatura_del_agua_del_mar_: %s\n" % e)
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

