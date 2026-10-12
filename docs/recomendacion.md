# Recomendación — ¿Los cuatro modos integrados resuelven el problema de movilidad?

**Periodo analizado:** 1 de junio al 15 de julio de 2026 (45 días) · **Fuente:** capa Gold
(`fct_abordajes`, `fct_viajes_metroriel`, `rpt_cobertura_zona`, `rpt_demanda_red`) ·
**Volumen:** 1,647,569 viajes (1,352,058 abordajes + 295,511 viajes completos de MetroRiel).

## Respuesta corta

**Parcialmente.** La red integrada llega a 15 de las 16 zonas donde vive la gente
del padrón y uno de cada dos usuarios ya combina modos, pero **deja una zona sin
servicio** y **el trazado propuesto de MetroRiel no va donde hoy está la mayor demanda**.

## Dónde sí

| Evidencia | Cifra |
|---|---:|
| Zonas con al menos un modo | **15 de 16** |
| Usuarios multimodales (2 o más modos) | **36,829 de 70,380 (52.3 %)** |
| Usuarios en 3 modos (Transmetro + Transurbano + MetroRiel) | 9,996 |
| Zonas con los 4 modos | Zona 17, Zona 12, Zona 1 |

- La integración ya se usa: la combinación más frecuente es **Transmetro + Transurbano
  (16,407 usuarios)**; MetroRiel se suma en 9,996 casos.
- Zona 17 y Zona 12 son la 3.ª y 5.ª zona con más demanda existente y tendrán los
  cuatro modos: ahí el trazado sí acierta.

## Dónde no

**1. Una zona sin servicio de ningún modo: Santa Catarina Pinula.** Tiene
**946 residentes activos** en el padrón (975 en total, tantos como Zona 1 o Zona 8) y
**0 abordajes** de los cuatro operadores. Es el corredor descubierto más claro.

**2. El MetroRiel no atiende donde más se necesita.** Medida sin contar la demanda
que el propio MetroRiel genera (Transmetro + Transurbano + Aerómetro):

| Ranking | Zona | Demanda existente | En trazado |
|---:|---|---:|:---:|
| 1 | Mixco | 132,768 | No |
| 2 | Zona 7 | 117,431 | No |
| 3 | Zona 17 | 94,799 | **Sí** |
| 5 | Zona 12 | 93,933 | **Sí** |
| 9 | Zona 1 | 83,367 | **Sí** |
| 11 | Zona 8 | 80,157 | **Sí** |
| 15 | Zona 6 | 71,840 | **Sí** |

- Las cinco zonas del trazado concentran el **31.4 %** de la demanda existente: menos que
  su peso en número de zonas servidas (5 de 15 = 33 %). Es decir, el trazado no prioriza
  demanda alta.
- **Zona 6 es la zona servida con menos demanda (puesto 15 de 15)** y Zona 8 está en el 11.
- Las dos zonas con más demanda, **Mixco y Zona 7**, quedan fuera; hoy dependen de buses
  y de Aerómetro (Aerómetro aporta 57,907 abordajes en Mixco y 43,808 en Zona 7).
- Zonas 4, 9, 10 y 11 solo tienen dos modos (Transmetro y Transurbano).

**3. La demanda está concentrada en el tiempo.** El **49.7 %** de los viajes ocurre en las
6 horas pico y solo las 7:00 y las 17:00 suman el **22.1 %** (máximo: 162,014 abordajes a
las 7:00). Un día hábil tiene **41,734** viajes, contra 22,530 en fin de semana.

## Recomendación

1. **Estación de transbordo en Zona 17.** Es la zona con más viajes de toda la red
   (**148,554** contando MetroRiel), la de mayor demanda existente dentro del trazado
   (puesto 3) y una de las tres donde coinciden los cuatro modos. Integrar ahí tarifa y
   andenes atiende directamente a los 36,829 usuarios que ya combinan modos; Zona 12
   (147,903 viajes, también con los cuatro modos) es la alternativa.
2. **Revisar el extremo Zona 6 – Zona 8 del MetroRiel** antes de comprometer obra: es el
   tramo con menor demanda existente (puestos 15 y 11), aunque hoy sea el par
   origen-destino con más viajes de MetroRiel (Zona 6 → Zona 8: 16,131). Evaluar desviar o
   extender hacia **Zona 7 – Mixco**, que suman **250,199** abordajes sin MetroRiel.
3. **Cubrir Santa Catarina Pinula** con una ruta alimentadora de Transurbano hacia
   Zona 10 o Zona 13: 946 tarjetas activas sin ningún punto de servicio.
4. **Reforzar frecuencia de 6:00 a 9:00 y de 16:00 a 19:00**, donde se concentra la
   mitad de la demanda.

## Límites de esta recomendación

- El padrón solo existe para Transmetro, por lo que "residentes" se basa en ~17,400
  tarjetas, no en la población total.
- La identidad de Aerómetro (hash) no se puede enlazar con las demás tarjetas: sus
  usuarios nunca cuentan como multimodales, así que **36,829 es un mínimo**.
- Los datos son generados (escala 8 %) y cubren 45 días; las conclusiones valen para
  este periodo.
