# swagger_client.PrediccionesEspecificasApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**informacion_nivologica_**](PrediccionesEspecificasApi.md#informacion_nivologica_) | **GET** /api/prediccion/especifica/nivologica/{area} | Información nivológica.
[**prediccin_de_montaa__tiempo_actual_**](PrediccionesEspecificasApi.md#prediccin_de_montaa__tiempo_actual_) | **GET** /api/prediccion/especifica/montaña/pasada/area/{area}/dia/{dia} | Predicción de montaña. Tiempo actual.
[**prediccin_de_montaa__tiempo_pasado_**](PrediccionesEspecificasApi.md#prediccin_de_montaa__tiempo_pasado_) | **GET** /api/prediccion/especifica/montaña/pasada/area/{area} | Predicción de montaña. Tiempo pasado.
[**prediccin_de_radiacin_ultravioleta__uvi_**](PrediccionesEspecificasApi.md#prediccin_de_radiacin_ultravioleta__uvi_) | **GET** /api/prediccion/especifica/uvi/{dia} | Predicción de radiación ultravioleta (UVI).
[**prediccin_para_las_playas__tiempo_actual_**](PrediccionesEspecificasApi.md#prediccin_para_las_playas__tiempo_actual_) | **GET** /api/prediccion/especifica/playa/{playa} | Predicción para las playas. Tiempo actual.
[**prediccin_por_municipios_diaria__tiempo_actual_**](PrediccionesEspecificasApi.md#prediccin_por_municipios_diaria__tiempo_actual_) | **GET** /api/prediccion/especifica/municipio/diaria/{municipio} | Predicción por municipios diaria. Tiempo actual.
[**prediccin_por_municipios_horaria__tiempo_actual_**](PrediccionesEspecificasApi.md#prediccin_por_municipios_horaria__tiempo_actual_) | **GET** /api/prediccion/especifica/municipio/horaria/{municipio} | Predicción por municipios horaria. Tiempo actual.


# **informacion_nivologica_**
> Model200 informacion_nivologica_(area)

Información nivológica.

Información nivológica para la zona montañosa que se pasa como parámetro (area).

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
api_instance = swagger_client.PrediccionesEspecificasApi(swagger_client.ApiClient(configuration))
area = 'area_example' # str |  | Código de  Área Montañosa |  Área Montañosa | |----------|----------| | 0 | Pirineo Catalán  | | 1  | Pirineo Navarro y Aragonés

try:
    # Información nivológica.
    api_response = api_instance.informacion_nivologica_(area)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesEspecificasApi->informacion_nivologica_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **area** | **str**|  | Código de  Área Montañosa |  Área Montañosa | |----------|----------| | 0 | Pirineo Catalán  | | 1  | Pirineo Navarro y Aragonés | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_de_montaa__tiempo_actual_**
> Model200 prediccin_de_montaa__tiempo_actual_(area, dia)

Predicción de montaña. Tiempo actual.

Predicción meteorológica para la zona montañosa que se pasa como parámetro (area) con validez para el día (día).  Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesEspecificasApi(swagger_client.ApiClient(configuration))
area = 'area_example' # str |  | Código de Área Montañosa | Área Montañosa | |----------|----------| | peu1 | Picos de Europa   | | nav1  | Pirineo Navarro   | | arn1  | Pirineo Aragonés  | | cat1  | Pirineo Catalán   | | rio1  | Ibérica Riojana   | | arn2  | Ibérica Aragonesa   | | mad2  | Sierras de Guadarrama y Somosierra  | | gre1  | Sierra de Gredos   | | nev1  | Sierra Nevada
dia = 'dia_example' # str |  | Código de día | Día | |----------|----------| | 0 | día actual  | | 1  | d+1 (mañana)   | | 2  | d+2 (pasado mañana)  | | 3  | d+3 (siguente a pasado mañana)

try:
    # Predicción de montaña. Tiempo actual.
    api_response = api_instance.prediccin_de_montaa__tiempo_actual_(area, dia)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesEspecificasApi->prediccin_de_montaa__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **area** | **str**|  | Código de Área Montañosa | Área Montañosa | |----------|----------| | peu1 | Picos de Europa   | | nav1  | Pirineo Navarro   | | arn1  | Pirineo Aragonés  | | cat1  | Pirineo Catalán   | | rio1  | Ibérica Riojana   | | arn2  | Ibérica Aragonesa   | | mad2  | Sierras de Guadarrama y Somosierra  | | gre1  | Sierra de Gredos   | | nev1  | Sierra Nevada | 
 **dia** | **str**|  | Código de día | Día | |----------|----------| | 0 | día actual  | | 1  | d+1 (mañana)   | | 2  | d+2 (pasado mañana)  | | 3  | d+3 (siguente a pasado mañana) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_de_montaa__tiempo_pasado_**
> Model200 prediccin_de_montaa__tiempo_pasado_(area)

Predicción de montaña. Tiempo pasado.

Breve resumen con lo más significativo de las condiciones meteorológicas registradas en la zona de montaña que se pasa como parámetro (area) en las últimas 24-36 horas.

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
api_instance = swagger_client.PrediccionesEspecificasApi(swagger_client.ApiClient(configuration))
area = 'area_example' # str |  | Código de Área Montañosa | Área Montañosa | |----------|----------| | peu1 | Picos de Europa   | | nav1  | Pirineo Navarro   | | arn1  | Pirineo Aragonés  | | cat1  | Pirineo Catalán   | | rio1  | Ibérica Riojana   | | arn2  | Ibérica Aragonesa   | | mad2  | Sierras de Guadarrama y Somosierra  | | gre1  | Sierra de Gredos   | | nev1  | Sierra Nevada

try:
    # Predicción de montaña. Tiempo pasado.
    api_response = api_instance.prediccin_de_montaa__tiempo_pasado_(area)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesEspecificasApi->prediccin_de_montaa__tiempo_pasado_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **area** | **str**|  | Código de Área Montañosa | Área Montañosa | |----------|----------| | peu1 | Picos de Europa   | | nav1  | Pirineo Navarro   | | arn1  | Pirineo Aragonés  | | cat1  | Pirineo Catalán   | | rio1  | Ibérica Riojana   | | arn2  | Ibérica Aragonesa   | | mad2  | Sierras de Guadarrama y Somosierra  | | gre1  | Sierra de Gredos   | | nev1  | Sierra Nevada | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_de_radiacin_ultravioleta__uvi_**
> Model200 prediccin_de_radiacin_ultravioleta__uvi_(dia)

Predicción de radiación ultravioleta (UVI).

 Predicción de Índice de radiación UV máximo en condiciones de cielo despejado para el día seleccionado.

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
api_instance = swagger_client.PrediccionesEspecificasApi(swagger_client.ApiClient(configuration))
dia = 'dia_example' # str |  | Código de día | Día | |----------|----------| | 0 | día actual  | | 1  | d+1 (mañana)   | | 2  | d+2 (pasado mañana)  | | 3  | d+3 (dentro de 3 días) | | 4  | d+4 (dentro de 4 días)

try:
    # Predicción de radiación ultravioleta (UVI).
    api_response = api_instance.prediccin_de_radiacin_ultravioleta__uvi_(dia)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesEspecificasApi->prediccin_de_radiacin_ultravioleta__uvi_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dia** | **str**|  | Código de día | Día | |----------|----------| | 0 | día actual  | | 1  | d+1 (mañana)   | | 2  | d+2 (pasado mañana)  | | 3  | d+3 (dentro de 3 días) | | 4  | d+4 (dentro de 4 días) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_para_las_playas__tiempo_actual_**
> Model200 prediccin_para_las_playas__tiempo_actual_(playa)

Predicción para las playas. Tiempo actual.

La predicción diaria de la playa que se pasa como parámetro. Establece el estado de nubosidad para unas horas determinadas, las 11 y las 17 hora oficial. Se analiza también si se espera precipitación en el entorno de esas horas, entre las 08 y las 14 horas y entre las 14 y 20 horas.

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
api_instance = swagger_client.PrediccionesEspecificasApi(swagger_client.ApiClient(configuration))
playa = 'playa_example' # str | Código de playa   http://www.aemet.es/documentos/es/eltiempo/prediccion/playas/Playas_codigos.csv

try:
    # Predicción para las playas. Tiempo actual.
    api_response = api_instance.prediccin_para_las_playas__tiempo_actual_(playa)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesEspecificasApi->prediccin_para_las_playas__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **playa** | **str**| Código de playa   http://www.aemet.es/documentos/es/eltiempo/prediccion/playas/Playas_codigos.csv | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_por_municipios_diaria__tiempo_actual_**
> Model200 prediccin_por_municipios_diaria__tiempo_actual_(municipio)

Predicción por municipios diaria. Tiempo actual.

Predicción para el municipio que se pasa como parámetro (municipio). Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesEspecificasApi(swagger_client.ApiClient(configuration))
municipio = 'municipio_example' # str | Código de municipio   http://www.ine.es/daco/daco42/codmun/codmunmapa.htm

try:
    # Predicción por municipios diaria. Tiempo actual.
    api_response = api_instance.prediccin_por_municipios_diaria__tiempo_actual_(municipio)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesEspecificasApi->prediccin_por_municipios_diaria__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **municipio** | **str**| Código de municipio   http://www.ine.es/daco/daco42/codmun/codmunmapa.htm | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_por_municipios_horaria__tiempo_actual_**
> Model200 prediccin_por_municipios_horaria__tiempo_actual_(municipio)

Predicción por municipios horaria. Tiempo actual.

Predicción horaria para el municipio que se pasa como parámetro (municipio). Presenta la información de hora en hora hasta 48 horas.

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
api_instance = swagger_client.PrediccionesEspecificasApi(swagger_client.ApiClient(configuration))
municipio = 'municipio_example' # str | Código de municipio  http://www.ine.es/daco/daco42/codmun/codmunmapa.htm

try:
    # Predicción por municipios horaria. Tiempo actual.
    api_response = api_instance.prediccin_por_municipios_horaria__tiempo_actual_(municipio)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesEspecificasApi->prediccin_por_municipios_horaria__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **municipio** | **str**| Código de municipio  http://www.ine.es/daco/daco42/codmun/codmunmapa.htm | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

