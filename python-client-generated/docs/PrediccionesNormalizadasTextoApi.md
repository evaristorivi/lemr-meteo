# swagger_client.PrediccionesNormalizadasTextoApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**prediccin_ccaa_hoy__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_hoy__archivo_) | **GET** /api/prediccion/ccaa/hoy/{ccaa}/elaboracion/{fecha} | Predicción CCAA hoy. Archivo.
[**prediccin_ccaa_hoy__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_hoy__tiempo_actual_) | **GET** /api/prediccion/ccaa/hoy/{ccaa} | Predicción CCAA hoy. Tiempo actual.
[**prediccin_ccaa_maana__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_maana__archivo_) | **GET** /api/prediccion/ccaa/manana/{ccaa}/elaboracion/{fecha} | Predicción CCAA mañana. Archivo.
[**prediccin_ccaa_maana__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_maana__tiempo_actual_) | **GET** /api/prediccion/ccaa/manana/{ccaa} | Predicción CCAA mañana. Tiempo actual.
[**prediccin_ccaa_medio_plazo__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_medio_plazo__archivo_) | **GET** /api/prediccion/ccaa/medioplazo/{ccaa}/elaboracion/{fecha} | Predicción CCAA medio plazo. Archivo.
[**prediccin_ccaa_medio_plazo__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_medio_plazo__tiempo_actual_) | **GET** /api/prediccion/ccaa/medioplazo/{ccaa} | Predicción CCAA medio plazo. Tiempo actual.
[**prediccin_ccaa_pasado_maana__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_pasado_maana__archivo_) | **GET** /api/prediccion/ccaa/pasadomanana/{ccaa}/elaboracion/{fecha} | Predicción CCAA pasado mañana. Archivo.
[**prediccin_ccaa_pasado_maana__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_ccaa_pasado_maana__tiempo_actual_) | **GET** /api/prediccion/ccaa/pasadomanana/{ccaa} | Predicción CCAA pasado mañana. Tiempo actual.
[**prediccin_nacional_hoy__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_hoy__archivo_) | **GET** /api/prediccion/nacional/hoy/elaboracion/{fecha} | Predicción nacional hoy. Archivo.
[**prediccin_nacional_hoy__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_hoy__tiempo_actual_) | **GET** /api/prediccion/nacional/hoy | Predicción nacional hoy. Última elaborada.
[**prediccin_nacional_maana__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_maana__archivo_) | **GET** /api/prediccion/nacional/manana/elaboracion/{fecha} | Predicción nacional mañana. Archivo.
[**prediccin_nacional_maana__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_maana__tiempo_actual_) | **GET** /api/prediccion/nacional/manana | Predicción nacional mañana. Tiempo actual.
[**prediccin_nacional_medio_plazo__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_medio_plazo__archivo_) | **GET** /api/prediccion/nacional/medioplazo/elaboracion/{fecha} | Predicción nacional medio plazo. Archivo.
[**prediccin_nacional_medio_plazo__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_medio_plazo__tiempo_actual_) | **GET** /api/prediccion/nacional/medioplazo | Predicción nacional medio plazo. Tiempo actual.
[**prediccin_nacional_pasado_maana__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_pasado_maana__archivo_) | **GET** /api/prediccion/nacional/pasadomanana/elaboracion/{fecha} | Predicción nacional pasado mañana. Archivo.
[**prediccin_nacional_pasado_maana__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_pasado_maana__tiempo_actual_) | **GET** /api/prediccion/nacional/pasadomanana | Predicción nacional pasado mañana. Tiempo actual.
[**prediccin_nacional_tendencia__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_tendencia__archivo_) | **GET** /api/prediccion/nacional/tendencia/elaboracion/{fecha} | Predicción nacional tendencia. Archivo.
[**prediccin_nacional_tendencia__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_nacional_tendencia__tiempo_actual_) | **GET** /api/prediccion/nacional/tendencia | Predicción nacional tendencia. Tiempo actual.
[**prediccin_provincia_hoy__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_provincia_hoy__archivo_) | **GET** /api/prediccion/provincia/hoy/{provincia}/elaboracion/{fecha} | Predicción provincia hoy. Archivo.
[**prediccin_provincia_hoy__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_provincia_hoy__tiempo_actual_) | **GET** /api/prediccion/provincia/hoy/{provincia} | Predicción provincia hoy. Tiempo actual.
[**prediccin_provincia_maana__archivo_**](PrediccionesNormalizadasTextoApi.md#prediccin_provincia_maana__archivo_) | **GET** /api/prediccion/provincia/manana/{provincia}/elaboracion/{fecha} | Predicción provincia mañana. Archivo.
[**prediccin_provincia_maana__tiempo_actual_**](PrediccionesNormalizadasTextoApi.md#prediccin_provincia_maana__tiempo_actual_) | **GET** /api/prediccion/provincia/manana/{provincia} | Predicción provincia mañana. Tiempo actual.


# **prediccin_ccaa_hoy__archivo_**
> Model200 prediccin_ccaa_hoy__archivo_(ccaa, fecha)

Predicción CCAA hoy. Archivo.

Predicción para la comunidad autónoma que se pasa como parámetro (ccaa) con validez para el día de fecha de elaboración que se pasa como parámetro (fecha). Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La   
fecha = 'fecha_example' # str | Día de elaboración (AAAA-MM-DD)

try:
    # Predicción CCAA hoy. Archivo.
    api_response = api_instance.prediccin_ccaa_hoy__archivo_(ccaa, fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_hoy__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La    | 
 **fecha** | **str**| Día de elaboración (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_ccaa_hoy__tiempo_actual_**
> Model200 prediccin_ccaa_hoy__tiempo_actual_(ccaa)

Predicción CCAA hoy. Tiempo actual.

Predicción para la CCAA que se pasa como parámetro con validez para mismo día que la fecha de petición. En el caso de que en la fecha de petición este producto todavía no se hubiera elaborado, se retornará el último elaborado. Actualización continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Asturias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La

try:
    # Predicción CCAA hoy. Tiempo actual.
    api_response = api_instance.prediccin_ccaa_hoy__tiempo_actual_(ccaa)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_hoy__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Asturias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_ccaa_maana__archivo_**
> Model200 prediccin_ccaa_maana__archivo_(ccaa, fecha)

Predicción CCAA mañana. Archivo.

Predicción para la comunidad autónoma que se pasa como parámetro (ccaa) con validez para el día siguiente a la fecha de elaboración que se pasa como parámetro (fecha). Periodicidad de actualización. continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La   
fecha = 'fecha_example' # str | Día de elaboración (AAAA-MM-DD)

try:
    # Predicción CCAA mañana. Archivo.
    api_response = api_instance.prediccin_ccaa_maana__archivo_(ccaa, fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_maana__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La    | 
 **fecha** | **str**| Día de elaboración (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_ccaa_maana__tiempo_actual_**
> Model200 prediccin_ccaa_maana__tiempo_actual_(ccaa)

Predicción CCAA mañana. Tiempo actual.

Predicción para la comunidad autónoma que se pasa como parámetro para el día siguiente a la fecha de la petición. En el caso de el producto no se hubiera elaborado todavía en la fecha de petición se retornará el último producto elaborado. Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La   

try:
    # Predicción CCAA mañana. Tiempo actual.
    api_response = api_instance.prediccin_ccaa_maana__tiempo_actual_(ccaa)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_maana__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_ccaa_medio_plazo__archivo_**
> Model200 prediccin_ccaa_medio_plazo__archivo_(ccaa, fecha)

Predicción CCAA medio plazo. Archivo.

Predicción de mediio plazo para la comunidad autónoma que se pasa como parámetro (ccaa) a partir de la fecha de elaboración que se pasa como parámetro (fecha). Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La   
fecha = 'fecha_example' # str | Día de elaboración (AAAA-MM-DD)

try:
    # Predicción CCAA medio plazo. Archivo.
    api_response = api_instance.prediccin_ccaa_medio_plazo__archivo_(ccaa, fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_medio_plazo__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La    | 
 **fecha** | **str**| Día de elaboración (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_ccaa_medio_plazo__tiempo_actual_**
> Model200 prediccin_ccaa_medio_plazo__tiempo_actual_(ccaa)

Predicción CCAA medio plazo. Tiempo actual.

Predicción para la comunidad autónoma que se pasa como parámetro (ccaa) y con validez para el medio plazo a partir de la fecha de petición. En el caso de que en el fecha de la petición no se hubiera generado aún el producto, se retornará el última elaborado. Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La   

try:
    # Predicción CCAA medio plazo. Tiempo actual.
    api_response = api_instance.prediccin_ccaa_medio_plazo__tiempo_actual_(ccaa)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_medio_plazo__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_ccaa_pasado_maana__archivo_**
> Model200 prediccin_ccaa_pasado_maana__archivo_(ccaa, fecha)

Predicción CCAA pasado mañana. Archivo.

Predicción para la comunidad autónoma que se pasa como parámetro (ccaa) y validez para pasado mañana a partir de la fecha de elaboración que se pasa como parámetro (fecha). Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La   
fecha = 'fecha_example' # str | Día de elaboración (AAAA-MM-DD)

try:
    # Predicción CCAA pasado mañana. Archivo.
    api_response = api_instance.prediccin_ccaa_pasado_maana__archivo_(ccaa, fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_pasado_maana__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La    | 
 **fecha** | **str**| Día de elaboración (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_ccaa_pasado_maana__tiempo_actual_**
> Model200 prediccin_ccaa_pasado_maana__tiempo_actual_(ccaa)

Predicción CCAA pasado mañana. Tiempo actual.

Predicción para la comunidad autónoma que se pasa como parámetro (ccaa) y validez para el medio plazo a partir de la fecha de la petición. En el caso de que en la fecha de la petición dicho producto aún no se hubiera generado retornará el último de este tipo que se hubiera generado.  Periodicidad de actualización: continuamente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
ccaa = 'ccaa_example' # str |  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La   

try:
    # Predicción CCAA pasado mañana. Tiempo actual.
    api_response = api_instance.prediccin_ccaa_pasado_maana__tiempo_actual_(ccaa)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_ccaa_pasado_maana__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ccaa** | **str**|  | Código de CCAA | CCAA | |----------|----------| | and  | Andalucía   | | arn  | Aragón   | | ast  | Astrrias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La    | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_nacional_hoy__archivo_**
> Model200 prediccin_nacional_hoy__archivo_(fecha)

Predicción nacional hoy. Archivo.

Predicción nacional para el día correspondiente a la fecha que se pasa como parámetro en en formato texto. Actualización diaria. Hay días en los que este producto no se realiza. En ese caso se devuelve un 404 producto no existente.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
fecha = 'fecha_example' # str | Fecha en formato (AAAA-MM-DD)

try:
    # Predicción nacional hoy. Archivo.
    api_response = api_instance.prediccin_nacional_hoy__archivo_(fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_hoy__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha** | **str**| Fecha en formato (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_nacional_hoy__tiempo_actual_**
> Model200 prediccin_nacional_hoy__tiempo_actual_()

Predicción nacional hoy. Última elaborada.

Predicción nacional para el día actual a la fecha de elaboración en formato texto. Actualización diaria. Hay días en los que este producto no se realiza. En ese caso se devuelve la predicción nacional última que se elaboró.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))

try:
    # Predicción nacional hoy. Última elaborada.
    api_response = api_instance.prediccin_nacional_hoy__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_hoy__tiempo_actual_: %s\n" % e)
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

# **prediccin_nacional_maana__archivo_**
> Model200 prediccin_nacional_maana__archivo_(fecha)

Predicción nacional mañana. Archivo.

Predicción nacional para el día siguiente a la fecha de elaboración. En este caso la fecha de elaboración es la fecha que se pasa como parámetro. Actualización diaria.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
fecha = 'fecha_example' # str | Día (AAAA-MM-DD)

try:
    # Predicción nacional mañana. Archivo.
    api_response = api_instance.prediccin_nacional_maana__archivo_(fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_maana__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha** | **str**| Día (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_nacional_maana__tiempo_actual_**
> Model200 prediccin_nacional_maana__tiempo_actual_()

Predicción nacional mañana. Tiempo actual.

Predicción nacional para el día siguiente a la fecha de elaboración. En este caso la fecha de elaboración es el día actual. Actualización diaria. En el caso de que en el día actual  todavía no se haya elaborado se devolverá el último producto de predicción nacional para mañana elaborado.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))

try:
    # Predicción nacional mañana. Tiempo actual.
    api_response = api_instance.prediccin_nacional_maana__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_maana__tiempo_actual_: %s\n" % e)
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

# **prediccin_nacional_medio_plazo__archivo_**
> Model200 prediccin_nacional_medio_plazo__archivo_(fecha)

Predicción nacional medio plazo. Archivo.

Predicción nacional para el medio plazo siguiente a la fecha de elaboración. En este caso, la fecha de elaboración es la fecha que se pasa como parámetro. Actualización diaria.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
fecha = 'fecha_example' # str | Día (AAAA-MM-DD)

try:
    # Predicción nacional medio plazo. Archivo.
    api_response = api_instance.prediccin_nacional_medio_plazo__archivo_(fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_medio_plazo__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha** | **str**| Día (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_nacional_medio_plazo__tiempo_actual_**
> Model200 prediccin_nacional_medio_plazo__tiempo_actual_()

Predicción nacional medio plazo. Tiempo actual.

Predicción nacional para medio plazo siguiente a la fecha de elaboración. En este caso la fecha de elaboración es el día actual. Actualización diaria. En el caso de que en el día actual  todavía no se haya elaborado se devolverá el último producto de predicción nacional para medio plazo elaborado.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))

try:
    # Predicción nacional medio plazo. Tiempo actual.
    api_response = api_instance.prediccin_nacional_medio_plazo__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_medio_plazo__tiempo_actual_: %s\n" % e)
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

# **prediccin_nacional_pasado_maana__archivo_**
> Model200 prediccin_nacional_pasado_maana__archivo_(fecha)

Predicción nacional pasado mañana. Archivo.

Predicción nacional para pasado mañana siguiente a la fecha de elaboración. En este caso, la fecha de elaboración es la fecha que se pasa como parámetro. Actualización diaria.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
fecha = 'fecha_example' # str | Día (AAAA-MM-DD)

try:
    # Predicción nacional pasado mañana. Archivo.
    api_response = api_instance.prediccin_nacional_pasado_maana__archivo_(fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_pasado_maana__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha** | **str**| Día (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_nacional_pasado_maana__tiempo_actual_**
> Model200 prediccin_nacional_pasado_maana__tiempo_actual_()

Predicción nacional pasado mañana. Tiempo actual.

Predicción nacional para pasado mañana siguiente a la fecha de elaboración. En este caso la fecha de elaboración es el día actual. Actualización diaria. En el caso de que en el día actual  todavía no se haya elaborado se devolverá el último producto de predicción nacional para pasado mañana elaborado.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))

try:
    # Predicción nacional pasado mañana. Tiempo actual.
    api_response = api_instance.prediccin_nacional_pasado_maana__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_pasado_maana__tiempo_actual_: %s\n" % e)
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

# **prediccin_nacional_tendencia__archivo_**
> Model200 prediccin_nacional_tendencia__archivo_(fecha)

Predicción nacional tendencia. Archivo.

Predicción nacional para tendencia siguiente a la fecha de elaboración. En este caso, la fecha de elaboración es la fecha que se pasa como parámetro. Actualización diaria.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
fecha = 'fecha_example' # str | Día (AAAA-MM-DD)

try:
    # Predicción nacional tendencia. Archivo.
    api_response = api_instance.prediccin_nacional_tendencia__archivo_(fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_tendencia__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha** | **str**| Día (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_nacional_tendencia__tiempo_actual_**
> Model200 prediccin_nacional_tendencia__tiempo_actual_()

Predicción nacional tendencia. Tiempo actual.

Predicción nacional para tendencia siguiente a la fecha de elaboración. En este caso la fecha de elaboración es el día actual. Actualización diaria. En el caso de que en el día actual  todavía no se haya elaborado se devolverá el último producto de predicción nacional para tendencia elaborado.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))

try:
    # Predicción nacional tendencia. Tiempo actual.
    api_response = api_instance.prediccin_nacional_tendencia__tiempo_actual_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_nacional_tendencia__tiempo_actual_: %s\n" % e)
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

# **prediccin_provincia_hoy__archivo_**
> Model200 prediccin_provincia_hoy__archivo_(provincia, fecha)

Predicción provincia hoy. Archivo.

Predicción del día siguiente a la fecha que se pasa como parámetro para la provincia que se pasa como parámetro. Actualización continua y fija a las 14:00 Hora Oficial Peninsular del día que se pasa como parámetro.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
provincia = 'provincia_example' # str |  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | | 
fecha = 'fecha_example' # str | Día de elaboración (AAAA-MM-DD)

try:
    # Predicción provincia hoy. Archivo.
    api_response = api_instance.prediccin_provincia_hoy__archivo_(provincia, fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_provincia_hoy__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **provincia** | **str**|  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | |  | 
 **fecha** | **str**| Día de elaboración (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_provincia_hoy__tiempo_actual_**
> Model200 prediccin_provincia_hoy__tiempo_actual_(provincia)

Predicción provincia hoy. Tiempo actual.

Predicción del día actual para la provincia que se pasa como parámetro. En el caso de que este producto no se haya elaborado todavía en el día actual, se retorna el último elaborado. Actualización continua y fija a las 14:00 Hora Oficial Peninsular.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
provincia = 'provincia_example' # str |  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | | 

try:
    # Predicción provincia hoy. Tiempo actual.
    api_response = api_instance.prediccin_provincia_hoy__tiempo_actual_(provincia)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_provincia_hoy__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **provincia** | **str**|  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | |  | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_provincia_maana__archivo_**
> Model200 prediccin_provincia_maana__archivo_(provincia, fecha)

Predicción provincia mañana. Archivo.

Predicción del día siguiente a la fecha que se pasa como parámetro para la provincia que se pasa como parámetro. Actualización continua y fija a las 14:00 Hora Oficial Peninsular del día que se pasa como parámetro.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
provincia = 'provincia_example' # str |  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | | 
fecha = 'fecha_example' # str | Día de elaboración (AAAA-MM-DD)

try:
    # Predicción provincia mañana. Archivo.
    api_response = api_instance.prediccin_provincia_maana__archivo_(provincia, fecha)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_provincia_maana__archivo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **provincia** | **str**|  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | |  | 
 **fecha** | **str**| Día de elaboración (AAAA-MM-DD) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **prediccin_provincia_maana__tiempo_actual_**
> Model200 prediccin_provincia_maana__tiempo_actual_(provincia)

Predicción provincia mañana. Tiempo actual.

Predicción del día siguiente para la provincia que se pasa como parámetro. En el caso de que este producto no se haya elaborado todavía en el día actual, se retorna el último elaborado. Actualización continua y fija a las 14:00 Hora Oficial Peninsular.

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
api_instance = swagger_client.PrediccionesNormalizadasTextoApi(swagger_client.ApiClient(configuration))
provincia = 'provincia_example' # str |  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | | 

try:
    # Predicción provincia mañana. Tiempo actual.
    api_response = api_instance.prediccin_provincia_maana__tiempo_actual_(provincia)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrediccionesNormalizadasTextoApi->prediccin_provincia_maana__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **provincia** | **str**|  | Código Provincia | Provincia | |----------|----------| | 01  | Araba/Álaba   | | 01  | Araba/Álava   | | 02  | Albacete   | | 03  | Alacant/Alicante  | | 04  | Almería   | | 33  | Asturias   | | 05  | Ávila   | | 06  | Badajoz   | | 07  | Illes Ballears   | | 08  | Barcelona   | | 48  | Bizkaia   | | 09  | Burgos   | | 10  | Cáceres   | | 11  | Cádiz   | | 39  | Cantabria   | | 12  | Castelló/Castellón   | | 51  | Ceuta   | | 13  | Ciudad Real   | | 14  | Córdoba   | | 15  | A Coruña   | | 16  | Cuenca   | | 17  | Girona   | | 18  | Granada   | | 19  | Guadalajara   | | 20  | Gipuzkoa   | | 21  | Huelva   | | 22  | Huesca   | | 23  | Jaén   | | 24  | León   | | 25  | Lleida   | | 27  | Lugo   | | 28  | Madrid   | | 29  | Málaga   | | 52  | Melilla   | | 30  | Murcia   | | 31  | Navarra   | | 32  | Oursense   | | 34  | Palencia   | | 35  | Las Palmas   | | 36  | Pontevedra   | | 26  | La Rioja   | | 37  | Salamanca   | | 38  | Santa Cruz de Tenerife   | | 40  | Segovia   | | 41  | Sevilla   | | 42  | Soria   | | 43  | Tarragona   | | 44  | Teruel   | | 45  | Toledo   | | 46  | València/Valencia   | | 47  | Valladolid   | | 49  | Zamora   | | 50  | Zaragoza   | |  | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

