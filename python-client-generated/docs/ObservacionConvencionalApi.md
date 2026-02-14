# swagger_client.ObservacionConvencionalApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**datos_de_observacin__tiempo_actual_**](ObservacionConvencionalApi.md#datos_de_observacin__tiempo_actual_) | **GET** /api/observacion/convencional/todas | Datos de observación. Tiempo actual.
[**datos_de_observacin__tiempo_actual_1**](ObservacionConvencionalApi.md#datos_de_observacin__tiempo_actual_1) | **GET** /api/observacion/convencional/datos/estacion/{idema} | Datos de observación. Tiempo actual.
[**mensajes_de_observacin__ltimo_elaborado_**](ObservacionConvencionalApi.md#mensajes_de_observacin__ltimo_elaborado_) | **GET** /api/observacion/convencional/mensajes/tipomensaje/{tipomensaje} | Mensajes de observación. Último elaborado.


# **datos_de_observacin__tiempo_actual_**
> Model200 datos_de_observacin__tiempo_actual_()

Datos de observación. Tiempo actual.

Datos de observación horarios de las últimas 24 horas todas las estaciones meteorológicas de las que se han recibido datos en ese período. Frecuencia de actualización: continuamente.

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
api_instance = swagger_client.ObservacionConvencionalApi(swagger_client.ApiClient(configuration))

try:
    # Datos de observación. Tiempo actual.
    api_response = api_instance.datos_de_observacin__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ObservacionConvencionalApi->datos_de_observacin__tiempo_actual_: %s\n" % e)
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

# **datos_de_observacin__tiempo_actual_1**
> Model200 datos_de_observacin__tiempo_actual_1(idema)

Datos de observación. Tiempo actual.

Datos de observación horarios de las últimas 24 horas de la estación meterológica que se pasa como parámetro (idema). Frecuencia de actualización: continuamente.

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
api_instance = swagger_client.ObservacionConvencionalApi(swagger_client.ApiClient(configuration))
idema = 'idema_example' # str | Índicativo climatológico de la EMA

try:
    # Datos de observación. Tiempo actual.
    api_response = api_instance.datos_de_observacin__tiempo_actual_1(idema)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ObservacionConvencionalApi->datos_de_observacin__tiempo_actual_1: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **idema** | **str**| Índicativo climatológico de la EMA | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **mensajes_de_observacin__ltimo_elaborado_**
> Model200 mensajes_de_observacin__ltimo_elaborado_(tipomensaje)

Mensajes de observación. Último elaborado.

Últimos mensajes de observación. Para los SYNOP y TEMP devuelve los mensajes de las últimas 24 horas y para los CLIMAT de los 40 últimos dias. Se pasa como parámetro el tipo de mensaje que se desea (tipomensaje). El resultado de la petición es un fichero en formato tar.gz, que contiene los boletines en formato json y bufr.

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
api_instance = swagger_client.ObservacionConvencionalApi(swagger_client.ApiClient(configuration))
tipomensaje = 'tipomensaje_example' # str |  | Código | Tipo de Mensaje | |----------|----------| | climat  | CLIMAT   | | synop  | SYNOP   | | temp  | TEMP  

try:
    # Mensajes de observación. Último elaborado.
    api_response = api_instance.mensajes_de_observacin__ltimo_elaborado_(tipomensaje)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ObservacionConvencionalApi->mensajes_de_observacin__ltimo_elaborado_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tipomensaje** | **str**|  | Código | Tipo de Mensaje | |----------|----------| | climat  | CLIMAT   | | synop  | SYNOP   | | temp  | TEMP   | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

