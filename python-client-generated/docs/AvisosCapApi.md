# swagger_client.AvisosCapApi

All URIs are relative to *https://opendata.aemet.es/opendata*

Method | HTTP request | Description
------------- | ------------- | -------------
[**avisos_de_fenmenos_meteorolgicos_adversos__archivo**](AvisosCapApi.md#avisos_de_fenmenos_meteorolgicos_adversos__archivo) | **GET** /api/avisos_cap/archivo/fechaini/{fechaIniStr}/fechafin/{fechaFinStr} | Avisos de Fenómenos Meteorológicos Adversos. Archivo.
[**avisos_de_fenmenos_meteorolgicos_adversos__ltimo_**](AvisosCapApi.md#avisos_de_fenmenos_meteorolgicos_adversos__ltimo_) | **GET** /api/avisos_cap/ultimoelaborado/area/{area} | Avisos de Fenómenos Meteorológicos Adversos. Último.


# **avisos_de_fenmenos_meteorolgicos_adversos__archivo**
> Model200 avisos_de_fenmenos_meteorolgicos_adversos__archivo(fecha_ini_str, fecha_fin_str)

Avisos de Fenómenos Meteorológicos Adversos. Archivo.

 Avisos de Fenómenos Meteorológicos adversos para el rango de fechas seleccionado (datos desde 18/06/2018).

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
api_instance = swagger_client.AvisosCapApi(swagger_client.ApiClient(configuration))
fecha_ini_str = 'fecha_ini_str_example' # str | Fecha Inicial (AAAA-MM-DDTHH:MM:SSUTC)
fecha_fin_str = 'fecha_fin_str_example' # str | Fecha Final (AAAA-MM-DDTHH:MM:SSUTC)

try:
    # Avisos de Fenómenos Meteorológicos Adversos. Archivo.
    api_response = api_instance.avisos_de_fenmenos_meteorolgicos_adversos__archivo(fecha_ini_str, fecha_fin_str)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AvisosCapApi->avisos_de_fenmenos_meteorolgicos_adversos__archivo: %s\n" % e)
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

# **avisos_de_fenmenos_meteorolgicos_adversos__ltimo_**
> Model200 avisos_de_fenmenos_meteorolgicos_adversos__ltimo_(area)

Avisos de Fenómenos Meteorológicos Adversos. Último.

 Últimos Avisos de Fenómenos Meteorológicos adversos elaborado para el área seleccionada.

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
api_instance = swagger_client.AvisosCapApi(swagger_client.ApiClient(configuration))
area = 'area_example' # str |  | Código | Área | |----------|----------| | esp  | España| | 61  | Andalucía   | | 62  | Aragón   | | 63  | Asturias, Principado de  | | 64  | Ballears, Illes   | | 78  | Ceuta   | | 65  | Canarias   | | 66  | Cantabria   | | 67  | Castilla y León   | | 68  | Castilla - La Mancha   | | 69  | Cataluña   | | 77  | Comunitat Valenciana   | | 70  | Extremadura   | | 71  | Galicia   | | 72  | Madrid, Comunidad de    | | 79  | Melilla   | | 73  | Murcia, Región de   | | 74  | Navarra, Comunidad Foral de   | | 75  | País Vasco | | 76  | Rioja, La

try:
    # Avisos de Fenómenos Meteorológicos Adversos. Último.
    api_response = api_instance.avisos_de_fenmenos_meteorolgicos_adversos__ltimo_(area)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AvisosCapApi->avisos_de_fenmenos_meteorolgicos_adversos__ltimo_: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **area** | **str**|  | Código | Área | |----------|----------| | esp  | España| | 61  | Andalucía   | | 62  | Aragón   | | 63  | Asturias, Principado de  | | 64  | Ballears, Illes   | | 78  | Ceuta   | | 65  | Canarias   | | 66  | Cantabria   | | 67  | Castilla y León   | | 68  | Castilla - La Mancha   | | 69  | Cataluña   | | 77  | Comunitat Valenciana   | | 70  | Extremadura   | | 71  | Galicia   | | 72  | Madrid, Comunidad de    | | 79  | Melilla   | | 73  | Murcia, Región de   | | 74  | Navarra, Comunidad Foral de   | | 75  | País Vasco | | 76  | Rioja, La | 

### Return type

[**Model200**](Model200.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

