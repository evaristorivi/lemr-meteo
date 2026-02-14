# swagger_client.MapasYGraficosApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**mapas_de_anlisis__ltima_pasada_**](MapasYGraficosApi.md#mapas_de_anlisis__ltima_pasada_) | **GET** /api/mapasygraficos/analisis | Mapas de análisis. Última pasada.
[**mapas_significativos__tiempo_actual_**](MapasYGraficosApi.md#mapas_significativos__tiempo_actual_) | **GET** /api/mapasygraficos/mapassignificativos/fecha/{fecha}/{ambito}/{dia} | Mapas significativos. Tiempo actual.
[**mapas_significativos__tiempo_actual_1**](MapasYGraficosApi.md#mapas_significativos__tiempo_actual_1) | **GET** /api/mapasygraficos/mapassignificativos/{ambito}/{dia} | Mapas significativos. Tiempo actual.


# **mapas_de_anlisis__ltima_pasada_**
> Model200 mapas_de_anlisis__ltima_pasada_()

Mapas de análisis. Última pasada.

Estos mapas muestran la configuración de la presión en superficie usando isobaras (lineas de igual presión), áreas de alta (A, a) y baja (B, b) presión y los frentes en Europa y el Atlántico Norte.El mapa de análisis presenta el estado de la atmósfera a la hora correspondiente y los fenómenos más relevantes observados en España. Periodicidad de actualización: cada 12 horas (00, 12).

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
api_instance = swagger_client.MapasYGraficosApi(swagger_client.ApiClient(configuration))

try:
    # Mapas de análisis. Última pasada.
    api_response = api_instance.mapas_de_anlisis__ltima_pasada_()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MapasYGraficosApi->mapas_de_anlisis__ltima_pasada_: %s\n" % e)
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

# **mapas_significativos__tiempo_actual_**
> Model200 mapas_significativos__tiempo_actual_(fecha, ambito, dia)

Mapas significativos. Tiempo actual.

Mapas significativos de ámbito nacional o CCAA, para una fecha dada y ese mismo día (D+0),  al día siguiente (D+1) o a los dos días (D+2), en el periodo horario de (00_12) ó (12-24).

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
api_instance = swagger_client.MapasYGraficosApi(swagger_client.ApiClient(configuration))
fecha = 'fecha_example' # str | Fecha de elaboración (AAAA-MM-DD)
ambito = 'ambito_example' # str |  | Código | Ámbito | |----------|----------| | esp  | España| | and  | Andalucía   | | arn  | Aragón   | | ast  | Asturias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La
dia = 'dia_example' # str |  | Código de día | Día | |----------|----------| | a | D+0 (00-12)  | | b  | D+0 (00-12)   | |  c | D+1 (00-12)  | | d  | D+1 (12-24) | | e  | D+2 (00-12) | | f  | D+2 (12-24)

try:
    # Mapas significativos. Tiempo actual.
    api_response = api_instance.mapas_significativos__tiempo_actual_(fecha, ambito, dia)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MapasYGraficosApi->mapas_significativos__tiempo_actual_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fecha** | **str**| Fecha de elaboración (AAAA-MM-DD) | 
 **ambito** | **str**|  | Código | Ámbito | |----------|----------| | esp  | España| | and  | Andalucía   | | arn  | Aragón   | | ast  | Asturias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La | 
 **dia** | **str**|  | Código de día | Día | |----------|----------| | a | D+0 (00-12)  | | b  | D+0 (00-12)   | |  c | D+1 (00-12)  | | d  | D+1 (12-24) | | e  | D+2 (00-12) | | f  | D+2 (12-24) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **mapas_significativos__tiempo_actual_1**
> Model200 mapas_significativos__tiempo_actual_1(ambito, dia)

Mapas significativos. Tiempo actual.

Mapas significativos de ámbito nacional o CCAA, para el día actual (D+0),  al día siguiente (D+1) o a los dos días (D+2), en el periodo horario de (00_12) ó (12-24).

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
api_instance = swagger_client.MapasYGraficosApi(swagger_client.ApiClient(configuration))
ambito = 'ambito_example' # str |  | Código | Ámbito | |----------|----------| | esp  | España| | and  | Andalucía   | | arn  | Aragón   | | ast  | Asturias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La
dia = 'dia_example' # str |  | Código de día | Día | |----------|----------| | a | D+0 (00-12)  | | b  | D+0 (00-12)   | |  c | D+1 (00-12)  | | d  | D+1 (12-24) | | e  | D+2 (00-12) | | f  | D+2 (12-24)

try:
    # Mapas significativos. Tiempo actual.
    api_response = api_instance.mapas_significativos__tiempo_actual_1(ambito, dia)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MapasYGraficosApi->mapas_significativos__tiempo_actual_1: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ambito** | **str**|  | Código | Ámbito | |----------|----------| | esp  | España| | and  | Andalucía   | | arn  | Aragón   | | ast  | Asturias  | | bal  | Ballears, Illes   | | coo  | Canarias   | | can  | Cantabria   | | cle  | Castilla y León   | | clm  | Castilla - La Mancha   | | cat  | Cataluña   | | val  | Comunitat Valenciana   | | ext  | Extremadura   | | gal  | Galicia   | | mad  | Madrid, Comunidad de    | | mur  | Murcia, Región de   | | nav  | Navarra, Comunidad Foral de   | | pva  | País Vasco | | rio  | Rioja, La | 
 **dia** | **str**|  | Código de día | Día | |----------|----------| | a | D+0 (00-12)  | | b  | D+0 (00-12)   | |  c | D+1 (00-12)  | | d  | D+1 (12-24) | | e  | D+2 (00-12) | | f  | D+2 (12-24) | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

