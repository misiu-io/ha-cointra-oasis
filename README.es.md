# Cointra Oasis Tech

**Idioma:** Español | [English README](https://github.com/misiu-io/ha-cointra-oasis/blob/main/README.md)

Integración de **Home Assistant** para consultar, en modo de solo lectura, los datos de los sistemas de **agua caliente sanitaria (ACS) por aerotermia** Cointra Oasis Tech. Utiliza el mismo servicio en la nube de Ferroli que la aplicación móvil **Ferroli Home / Four Solid**.

Este es un pequeño proyecto personal y no oficial. No está afiliado, asociado, autorizado ni respaldado por Cointra o Ferroli.

**Qué permite consultar:** temperaturas del agua, modos de funcionamiento, consignas, estado de la programación y datos de diagnóstico. **No envía órdenes de control** ni modifica la configuración o los horarios del sistema de ACS.

**Requisitos:** Home Assistant 2026.11 o posterior y una cuenta operativa de Ferroli Home / Four Solid con el equipo ya registrado. La integración necesita conexión a Internet para acceder al servicio en la nube; no funciona mediante una conexión local.

<!-- ha-marketplace:exclude-start -->
## Instalación

1. En Home Assistant, abre **Ajustes → Marketplace → Añadir desde enlace**.
2. Añade el [repositorio Cointra Oasis Tech](https://github.com/misiu-io/ha-cointra-oasis): `https://github.com/misiu-io/ha-cointra-oasis`.
3. Abre **Cointra Oasis Tech** en Marketplace y selecciona **Instalar**.
4. Ve a **Ajustes → Dispositivos y servicios → Añadir integración** y selecciona **Cointra Oasis Tech**.

Puedes instalarla como repositorio personalizado en Marketplace. Todavía no figura en el catálogo público. Para actualizar una integración que ya está cargada, es necesario reiniciar Home Assistant.
<!-- ha-marketplace:exclude-end -->

## Configuración

Introduce la dirección de correo electrónico y la contraseña de tu cuenta de **Ferroli Home / Four Solid**. La integración obtiene los equipos registrados en esa cuenta. Si hay varios, puedes elegir cuál quieres monitorizar; si solo hay uno, se selecciona automáticamente. Home Assistant conserva el nombre que tenga en la aplicación móvil.

La integración se autentica con la API en la nube y consulta el estado completo del equipo cada **30 minutos** de forma predeterminada. Puedes cambiar el intervalo desde la opción **Configurar** de la integración.

Las credenciales se guardan en la entrada de configuración de Home Assistant para poder autenticar las consultas. Protege los archivos de configuración y las copias de seguridad de Home Assistant.

## Datos disponibles

| Grupo | Lecturas |
| --- | --- |
| Agua y temperaturas | Temperatura del agua, temperaturas de las sondas superior e inferior del depósito, temperatura de la batería / desescarche y temperatura del aire exterior |
| Funcionamiento | Modos solicitado y real, temperaturas de consigna solicitada y real |
| Programación | Programación activada, franja horaria activa e inicio y fin de la franja |
| Estados | Alarma, antilegionela, protección antihielo, fotovoltaica, red inteligente, solar térmica y modo silencioso |
| Diagnóstico | Última comunicación del equipo, versiones de firmware, dirección MAC del módulo Wi-Fi y estado de lectura de datos |

Todas las entidades son de solo lectura. Algunas lecturas pueden aparecer como no disponibles si tu modelo no proporciona esos datos.

## Compatibilidad y limitaciones

**Equipo probado:** Cointra Oasis Tech 200 HT, en mi propia instalación.

Cointra forma parte del Grupo Ferroli. La [declaración de conformidad del fabricante](https://www.cointra.es/wp-content/uploads/2023/10/declaracion-conformidad-oasis-tech.pdf) agrupa el Oasis Tech 200 HT con los modelos **Ferroli EGEA Tech 200 HT** y **Dora Tech 200 HT**. Parece que comparten una plataforma de producto y módulos Wi-Fi relacionados, pero **no he probado** esos otros modelos ni sus versiones de firmware. No se garantiza la compatibilidad. No se admiten equipos que utilicen Tuya / Smart Life.

**Sin control remoto:** Se evitan deliberadamente las operaciones de escritura. Algunas versiones de firmware pueden interpretar los comandos de forma diferente y se han comunicado casos en los que los intentos de control afectaron a la programación existente.

**Todavía sin estadísticas energéticas:** El servicio en la nube parece ofrecer datos de consumo y producción, pero no he conseguido obtener resultados fiables de forma consistente. Por ahora monitorizo el consumo eléctrico por separado mediante Shelly y otros equipos de medición.

**Dependencia de la nube:** La integración utiliza una API no oficial que puede cambiar sin previo aviso. Una caída del servicio, un cambio de autenticación o una respuesta no compatible podrían dejar temporalmente algunas entidades sin datos. Como ocurre con cualquier integración personalizada de terceros, no puedo garantizar su funcionamiento con todas las versiones de Home Assistant o de firmware.

## Por qué hice esta integración

En 2024, durante la reforma de una casa antigua en España, renové la fontanería y la instalación eléctrica e instalé un sistema de ACS por aerotermia de alta temperatura **Cointra Oasis Tech 200 HT**. Prácticamente todo lo demás en la casa está conectado a Home Assistant, así que me frustraba no poder consultar también allí sus temperaturas, el modo de funcionamiento y otros parámetros.

Investigé la conexión Modbus / cascada del controlador, pero no conseguí una tabla de registros utilizable ni confirmar una interfaz local adecuada. Por eso empecé a investigar la API de Ferroli utilizada por la aplicación móvil.

## Errores, pruebas y colaboración

Si pruebas la integración con otro modelo o versión de firmware, me interesa saber qué funciona. Puedes [abrir una incidencia en GitHub](https://github.com/misiu-io/ha-cointra-oasis/issues/new) e indicar el modelo, la aplicación móvil, las versiones de firmware de la placa principal, la pantalla y el módulo Wi-Fi, además de las lecturas o errores que observes. No incluyas credenciales, números de serie ni direcciones MAC.

Este proyecto sigue en una fase temprana y solo se ha probado en un equipo físico. Incluye pruebas automatizadas locales, pero no sustituyen las pruebas con dispositivos reales.

Para más información, consulta las [notas sobre la API](API.md) y el [registro de cambios](CHANGELOG.md).
