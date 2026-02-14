# swagger_client.ValoresClimatologicosApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**climatologas_diarias_**](ValoresClimatologicosApi.md#climatologas_diarias_) | **GET** /api/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema} | Climatologías diarias.
[**climatologas_diarias_1**](ValoresClimatologicosApi.md#climatologas_diarias_1) | **GET** /api/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/todasestaciones | Climatologías diarias.
[**climatologas_mensuales_anuales_**](ValoresClimatologicosApi.md#climatologas_mensuales_anuales_) | **GET** /api/valores/climatologicos/mensualesanuales/datos/anioini/{anioIniStr}/aniofin/{anioFinStr}/estacion/{idema} | Climatologías mensuales anuales.
[**climatologas_normales__19812010_**](ValoresClimatologicosApi.md#climatologas_normales__19812010_) | **GET** /api/valores/climatologicos/normales/estacion/{idema} | Climatologías normales (1981-2010).
[**estaciones_por_indicativo_**](ValoresClimatologicosApi.md#estaciones_por_indicativo_) | **GET** /api/valores/climatologicos/inventarioestaciones/estaciones/{estaciones} | Estaciones por indicativo.
[**inventario_de_estaciones__valores_climatolgicos_**](ValoresClimatologicosApi.md#inventario_de_estaciones__valores_climatolgicos_) | **GET** /api/valores/climatologicos/inventarioestaciones/todasestaciones | Inventario de estaciones (valores climatológicos).
[**valores_extremos_**](ValoresClimatologicosApi.md#valores_extremos_) | **GET** /api/valores/climatologicos/valoresextremos/parametro/{parametro}/estacion/{idema} | Valores extremos.


# **climatologas_diarias_**
> Model200 climatologas_diarias_(fecha_ini_str, fecha_fin_str, idema)

Climatologías diarias.

Valores climatológicos para el rango de fechas y la estación seleccionada. Periodicidad: 1 vez al día.

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
api_instance = swagger_client.ValoresClimatologicosApi(swagger_client.ApiClient(configuration))
fecha_ini_str = 'fecha_ini_str_example' # str | Fecha Inicial (AAAA-MM-DDTHH:MM:SSUTC)
fecha_fin_str = 'fecha_fin_str_example' # str | Fecha Final (AAAA-MM-DDTHH:MM:SSUTC)
idema = 'idema_example' # str | Indicativo climatológico de la EMA. Puede introducir varios indicativos separados por comas (,)

try:
    # Climatologías diarias.
    api_response = api_instance.climatologas_diarias_(fecha_ini_str, fecha_fin_str, idema)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValoresClimatologicosApi->climatologas_diarias_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha_ini_str** | **str**| Fecha Inicial (AAAA-MM-DDTHH:MM:SSUTC) | 
 **fecha_fin_str** | **str**| Fecha Final (AAAA-MM-DDTHH:MM:SSUTC) | 
 **idema** | **str**| Indicativo climatológico de la EMA. Puede introducir varios indicativos separados por comas (,) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **climatologas_diarias_1**
> Model200 climatologas_diarias_1(fecha_ini_str, fecha_fin_str)

Climatologías diarias.

Valores climatológicos de todas las estaciones para el rango de fechas seleccionado. Periodicidad: 1 vez al día.

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
api_instance = swagger_client.ValoresClimatologicosApi(swagger_client.ApiClient(configuration))
fecha_ini_str = 'fecha_ini_str_example' # str | Fecha Inicial (AAAA-MM-DDTHH:MM:SSUTC)
fecha_fin_str = 'fecha_fin_str_example' # str | Fecha Final (AAAA-MM-DDTHH:MM:SSUTC)

try:
    # Climatologías diarias.
    api_response = api_instance.climatologas_diarias_1(fecha_ini_str, fecha_fin_str)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValoresClimatologicosApi->climatologas_diarias_1: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha_ini_str** | **str**| Fecha Inicial (AAAA-MM-DDTHH:MM:SSUTC) | 
 **fecha_fin_str** | **str**| Fecha Final (AAAA-MM-DDTHH:MM:SSUTC) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **climatologas_mensuales_anuales_**
> Model200 climatologas_mensuales_anuales_(anio_ini_str, anio_fin_str, idema)

Climatologías mensuales anuales.

Valores medios mensuales y anuales de los datos climatológicos para la estación y el periodo de años pasados por parámetro. Periodicidad: 1 vez al día.

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
api_instance = swagger_client.ValoresClimatologicosApi(swagger_client.ApiClient(configuration))
anio_ini_str = 'anio_ini_str_example' # str | Año Inicial (AAAA)
anio_fin_str = 'anio_fin_str_example' # str | Año Final (AAAA)
idema = 'idema_example' # str | Indicativo climatológico de la EMA

try:
    # Climatologías mensuales anuales.
    api_response = api_instance.climatologas_mensuales_anuales_(anio_ini_str, anio_fin_str, idema)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValoresClimatologicosApi->climatologas_mensuales_anuales_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **anio_ini_str** | **str**| Año Inicial (AAAA) | 
 **anio_fin_str** | **str**| Año Final (AAAA) | 
 **idema** | **str**| Indicativo climatológico de la EMA | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **climatologas_normales__19812010_**
> Model200 climatologas_normales__19812010_(idema)

Climatologías normales (1981-2010).

Valores climatológicos normales (periodo 1981-2010) para la estación pasada por parámetro. Periodicidad: 1 vez al día.

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
api_instance = swagger_client.ValoresClimatologicosApi(swagger_client.ApiClient(configuration))
idema = 'idema_example' # str | Indicativo climatológico de la EMA

try:
    # Climatologías normales (1981-2010).
    api_response = api_instance.climatologas_normales__19812010_(idema)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValoresClimatologicosApi->climatologas_normales__19812010_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **idema** | **str**| Indicativo climatológico de la EMA | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **estaciones_por_indicativo_**
> Model200 estaciones_por_indicativo_(estaciones)

Estaciones por indicativo.

Características de la estación climatológica pasada por parámetro.

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
api_instance = swagger_client.ValoresClimatologicosApi(swagger_client.ApiClient(configuration))
estaciones = 'estaciones_example' # str | Listado de indicativos climatológicos (id1,id2,id3,...,idn)

try:
    # Estaciones por indicativo.
    api_response = api_instance.estaciones_por_indicativo_(estaciones)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValoresClimatologicosApi->estaciones_por_indicativo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **estaciones** | **str**| Listado de indicativos climatológicos (id1,id2,id3,...,idn) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **inventario_de_estaciones__valores_climatolgicos_**
> Model200 inventario_de_estaciones__valores_climatolgicos_()

Inventario de estaciones (valores climatológicos).

Inventario con las características de todas las estaciones climatológicas. Periodicidad: 1 vez al día.

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
api_instance = swagger_client.ValoresClimatologicosApi(swagger_client.ApiClient(configuration))

try:
    # Inventario de estaciones (valores climatológicos).
    api_response = api_instance.inventario_de_estaciones__valores_climatolgicos_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValoresClimatologicosApi->inventario_de_estaciones__valores_climatolgicos_: %s\n" % e)
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

# **valores_extremos_**
> Model200 valores_extremos_(parametro, idema)

Valores extremos.

Valores extremos para la estación y la variable (precipitación, temperatura y viento) pasadas por parámetro. Periodicidad: 1 vez al día.

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
api_instance = swagger_client.ValoresClimatologicosApi(swagger_client.ApiClient(configuration))
parametro = 'parametro_example' # str |  | Código | Parámetro Meteorológico | |----------|----------| | P  | Precipitación   | | T  | Temperatura   | | V  | Viento 
idema = 'idema_example' # str | Indicativo climatológico de la EMA

try:
    # Valores extremos.
    api_response = api_instance.valores_extremos_(parametro, idema)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValoresClimatologicosApi->valores_extremos_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parametro** | **str**|  | Código | Parámetro Meteorológico | |----------|----------| | P  | Precipitación   | | T  | Temperatura   | | V  | Viento  | 
 **idema** | **str**| Indicativo climatológico de la EMA | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

